/* eslint-disable */
/* tslint:disable */

/**
 * Mock Service Worker.
 * @see https://github.com/mswjs/msw
 * - 이 파일은 수정하지 마세요.
 */

const PACKAGE_VERSION = '2.12.13'
const INTEGRITY_CHECKSUM = '4db4a41e972cec1b64cc569c66952d82'
const IS_MOCKED_RESPONSE = Symbol('isMockedResponse')
const activeClientIds = new Set()

addEventListener('install', function () {
  self.skipWaiting()
})

addEventListener('activate', function (event) {
  event.waitUntil(self.clients.claim())
})

addEventListener('message', async function (event) {
  const clientId = Reflect.get(event.source || {}, 'id')

  if (!clientId || !self.clients) {
    return
  }

  const client = await self.clients.get(clientId)

  if (!client) {
    return
  }

  const allClients = await self.clients.matchAll({
    type: 'window',
  })

  switch (event.data) {
    case 'KEEPALIVE_REQUEST': {
      sendToClient(client, {
        type: 'KEEPALIVE_RESPONSE',
      })
      break
    }

    case 'INTEGRITY_CHECK_REQUEST': {
      sendToClient(client, {
        type: 'INTEGRITY_CHECK_RESPONSE',
        payload: {
          packageVersion: PACKAGE_VERSION,
          checksum: INTEGRITY_CHECKSUM,
        },
      })
      break
    }

    case 'MOCK_ACTIVATE': {
      activeClientIds.add(clientId)

      sendToClient(client, {
        type: 'MOCKING_ENABLED',
        payload: {
          client: {
            id: client.id,
            frameType: client.frameType,
          },
        },
      })
      break
    }

    case 'CLIENT_CLOSED': {
      activeClientIds.delete(clientId)

      const remainingClients = allClients.filter((client) => {
        return client.id !== clientId
      })

      // 클라이언트가 더 이상 없으면 자체 등록을 해제합니다.
      if (remainingClients.length === 0) {
        self.registration.unregister()
      }

      break
    }
  }
})

addEventListener('fetch', function (event) {
  const requestInterceptedAt = Date.now()

  // 브라우저 네비게이션(페이지 이동) 요청은 우회합니다.
  if (event.request.mode === 'navigate') {
    return
  }

  // DevTools를 열면 워커가 처리할 수 없는 "only-if-cached" 요청이 발생합니다.
  // 이러한 요청은 우회합니다.
  if (
    event.request.cache === 'only-if-cached' &&
    event.request.mode !== 'same-origin'
  ) {
    return
  }

  // 활성 클라이언트가 없으면 모든 요청을 우회합니다.
  // 종료된 후 자체 등록 취소된 워커가 요청을 처리하는 것을 방지합니다.
  // (다음 새로고침 때까지 계속 활성 상태로 유지됩니다).
  if (activeClientIds.size === 0) {
    return
  }

  const requestId = crypto.randomUUID()
  event.respondWith(handleRequest(event, requestId, requestInterceptedAt))
})

/**
 * @param {FetchEvent} event
 * @param {string} requestId
 * @param {number} requestInterceptedAt
 */
async function handleRequest(event, requestId, requestInterceptedAt) {
  const client = await resolveMainClient(event)
  const requestCloneForEvents = event.request.clone()
  const response = await getResponse(
    event,
    client,
    requestId,
    requestInterceptedAt,
  )

  // "response:*" 수명 주기 이벤트를 위해 복제된 응답을 다시 보냅니다.
  // MSW가 활성 상태이고 메시지를 처리할 준비가 되었는지 확인하세요.
  // 그렇지 않으면 이 메시지는 무기한 보류됩니다.
  if (client && activeClientIds.has(client.id)) {
    const serializedRequest = await serializeRequest(requestCloneForEvents)

    // 응답을 복제하여 클라이언트와 라이브러리 모두 사용할 수 있도록 합니다.
    const responseClone = response.clone()

    sendToClient(
      client,
      {
        type: 'RESPONSE',
        payload: {
          isMockedResponse: IS_MOCKED_RESPONSE in response,
          request: {
            id: requestId,
            ...serializedRequest,
          },
          response: {
            type: responseClone.type,
            status: responseClone.status,
            statusText: responseClone.statusText,
            headers: Object.fromEntries(responseClone.headers.entries()),
            body: responseClone.body,
          },
        },
      },
      responseClone.body ? [serializedRequest.body, responseClone.body] : [],
    )
  }

  return response
}

/**
 * 주어진 이벤트에 대한 메인 클라이언트를 확인합니다.
 * 요청을 발행하는 클라이언트가 반드시 워커를 등록한 클라이언트와 동일하지는 않습니다.
 * 응답 확인 단계 동안 워커는 후자와 통신해야 합니다.
 * @param {FetchEvent} event
 * @returns {Promise<Client | undefined>}
 */
async function resolveMainClient(event) {
  const client = await self.clients.get(event.clientId)

  if (activeClientIds.has(event.clientId)) {
    return client
  }

  if (client?.frameType === 'top-level') {
    return client
  }

  const allClients = await self.clients.matchAll({
    type: 'window',
  })

  return allClients
    .filter((client) => {
      // 현재 보이는 클라이언트만 가져옵니다.
      return client.visibilityState === 'visible'
    })
    .find((client) => {
      // 워커를 등록한 클라이언트 세트에 기록된 클라이언트 ID를 찾습니다.
      return activeClientIds.has(client.id)
    })
}

/**
 * @param {FetchEvent} event
 * @param {Client | undefined} client
 * @param {string} requestId
 * @param {number} requestInterceptedAt
 * @returns {Promise<Response>}
 */
async function getResponse(event, client, requestId, requestInterceptedAt) {
  // 요청이 이미 사용되었을 수 있으므로 복제합니다.
  // (예: 본문을 읽고 클라이언트로 보냄).
  const requestClone = event.request.clone()

  function passthrough() {
    // 헤더를 조작할 수 있도록 요청 헤더를 새로운 Headers 인스턴스로 캐스팅합니다.
    const headers = new Headers(requestClone.headers)

    // 이 요청을 패스스루로 표시한 "accept" 헤더 값을 제거합니다.
    // 이는 요청 변경을 방지하고 또한 사용자 정의 CORS 정책을 준수하도록 유지합니다.
    const acceptHeader = headers.get('accept')
    if (acceptHeader) {
      const values = acceptHeader.split(',').map((value) => value.trim())
      const filteredValues = values.filter(
        (value) => value !== 'msw/passthrough',
      )

      if (filteredValues.length > 0) {
        headers.set('accept', filteredValues.join(', '))
      } else {
        headers.delete('accept')
      }
    }

    return fetch(requestClone, { headers })
  }

  // 클라이언트가 비활성 상태일 때 모킹을 우회(설정된 API 통신)합니다.
  if (!client) {
    return passthrough()
  }

  // 초기 페이지 로드 요청(예: 정적 에셋 파일)을 우회합니다.
  // 활성 클라이언트 맵에 즉각적인/부모 클라이언트가 없다는 것은
  // MSW가 아직 "MOCK_ACTIVATE" 이벤트를 전달하지 않았고
  // 요청을 처리할 준비가 되지 않았음을 의미합니다.
  if (!activeClientIds.has(client.id)) {
    return passthrough()
  }

  // 클라이언트에게 요청이 가로채졌음을 알립니다.
  const serializedRequest = await serializeRequest(event.request)
  const clientMessage = await sendToClient(
    client,
    {
      type: 'REQUEST',
      payload: {
        id: requestId,
        interceptedAt: requestInterceptedAt,
        ...serializedRequest,
      },
    },
    [serializedRequest.body],
  )

  switch (clientMessage.type) {
    case 'MOCK_RESPONSE': {
      return respondWithMock(clientMessage.data)
    }

    case 'PASSTHROUGH': {
      return passthrough()
    }
  }

  return passthrough()
}

/**
 * @param {Client} client
 * @param {any} message
 * @param {Array<Transferable>} transferrables
 * @returns {Promise<any>}
 */
function sendToClient(client, message, transferrables = []) {
  return new Promise((resolve, reject) => {
    const channel = new MessageChannel()

    channel.port1.onmessage = (event) => {
      if (event.data && event.data.error) {
        return reject(event.data.error)
      }

      resolve(event.data)
    }

    client.postMessage(message, [
      channel.port2,
      ...transferrables.filter(Boolean),
    ])
  })
}

/**
 * @param {Response} response
 * @returns {Response}
 */
function respondWithMock(response) {
  // 응답 상태 코드를 0으로 설정하는 것은 아무 일도 하지 않습니다.
  // 그러나 "Response.error()"로 응답할 때, 생성된 응답
  // 인스턴스는 상태 코드가 0으로 설정됩니다. 상태 코드가 0인
  // 응답 인스턴스를 생성하는 것은 불가능하므로 해당 사용 사례를 별도로 처리합니다.
  if (response.status === 0) {
    return Response.error()
  }

  const mockedResponse = new Response(response.body, response)

  Reflect.defineProperty(mockedResponse, IS_MOCKED_RESPONSE, {
    value: true,
    enumerable: true,
  })

  return mockedResponse
}

/**
 * @param {Request} request
 */
async function serializeRequest(request) {
  return {
    url: request.url,
    mode: request.mode,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries()),
    cache: request.cache,
    credentials: request.credentials,
    destination: request.destination,
    integrity: request.integrity,
    redirect: request.redirect,
    referrer: request.referrer,
    referrerPolicy: request.referrerPolicy,
    body: await request.arrayBuffer(),
    keepalive: request.keepalive,
  }
}
