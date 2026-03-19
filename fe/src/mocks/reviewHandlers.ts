import { http, HttpResponse } from 'msw';

const API_BASE_URL = 'http://localhost:8080';

const reviewSeed = [
  {
    reviewId: 'e636cba2-f5a2-4161-a972-b9e2d7ac7975',
    rating: 5,
    content: '카페가 정말 예쁘네요!~~~~~~~~하하하',
    createdAt: '2026-03-18T13:21:08.446623',
    updatedAt: '2026-03-18T13:21:08.446623',
    images: [
      {
        imageId: 'e4fa8fd5-4f33-46be-8046-18a1b1582de8',
        imageUrl:
          'https://dqee7nuafmp2e.cloudfront.net/review/3cd3ac3e-b593-45a0-ad07-39c007152301_image-1.jpg',
      },
      {
        imageId: 'e984dc43-7b8d-414f-ba8c-c92f55b750c2',
        imageUrl:
          'https://dqee7nuafmp2e.cloudfront.net/review/80044a35-d709-4744-9a17-c501a3d50586_image-2.jpg',
      },
    ],
    nickname: '킴싸피',
  },
  {
    reviewId: '4f4ae9be-2857-4389-a534-3197567175a0',
    rating: 5,
    content: '분위기 좋고 커피도 맛있었어요.',
    createdAt: '2026-03-16T13:27:19.991701',
    updatedAt: '2026-03-16T13:27:19.991701',
    images: [
      {
        imageId: '2a348d01-b897-436b-a4f4-f80e3a082285',
        imageUrl: 'https://s3.cloud/test/image.png',
      },
    ],
    nickname: '킴싸피',
  },
  {
    reviewId: '1295ff18-3f84-4366-87b5-8212126825c7',
    rating: 3,
    content: '수정이요~~',
    createdAt: '2026-03-16T13:19:49.415999',
    updatedAt: '2026-03-16T13:26:31.179429',
    images: [],
    nickname: '킴싸피',
  },
  {
    reviewId: '95de77df-a40e-4f9d-82d7-d23549d0d101',
    rating: 4,
    content: '좌석 간격이 넓어서 대화하기 편했어요.',
    createdAt: '2026-03-15T09:12:11.000000',
    updatedAt: '2026-03-15T09:12:11.000000',
    images: [{ imageId: 'img-4', imageUrl: 'https://s3.cloud/test/cafe4.png' }],
    nickname: '하늘',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f001',
    rating: 4,
    content: '디저트가 생각보다 괜찮았어요.',
    createdAt: '2026-03-14T18:43:20.000000',
    updatedAt: '2026-03-14T18:43:20.000000',
    images: [],
    nickname: '모카',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f002',
    rating: 2,
    content: '주말엔 조금 시끄러운 편이에요.',
    createdAt: '2026-03-13T16:10:00.000000',
    updatedAt: '2026-03-13T16:10:00.000000',
    images: [{ imageId: 'img-6', imageUrl: 'https://s3.cloud/test/cafe6.png' }],
    nickname: '로이',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f003',
    rating: 5,
    content: '사진 찍기 좋은 포인트가 많네요.',
    createdAt: '2026-03-12T15:00:00.000000',
    updatedAt: '2026-03-12T15:00:00.000000',
    images: [{ imageId: 'img-7', imageUrl: 'https://s3.cloud/test/cafe7.png' }],
    nickname: '단비',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f004',
    rating: 4,
    content: '콘센트가 많아서 작업하기 좋았습니다.',
    createdAt: '2026-03-11T14:00:00.000000',
    updatedAt: '2026-03-11T14:00:00.000000',
    images: [],
    nickname: '한결',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f005',
    rating: 5,
    content: '재방문 의사 있어요.',
    createdAt: '2026-03-10T08:30:00.000000',
    updatedAt: '2026-03-10T08:30:00.000000',
    images: [{ imageId: 'img-9', imageUrl: 'https://s3.cloud/test/cafe9.png' }],
    nickname: '예나',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f006',
    rating: 3,
    content: '무난했지만 특별한 포인트는 적었어요.',
    createdAt: '2026-03-09T12:50:00.000000',
    updatedAt: '2026-03-09T12:50:00.000000',
    images: [],
    nickname: '유진',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f007',
    rating: 4,
    content: '음악 볼륨이 적당해서 오래 머물렀습니다.',
    createdAt: '2026-03-08T11:22:00.000000',
    updatedAt: '2026-03-08T11:22:00.000000',
    images: [],
    nickname: '민수',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f008',
    rating: 5,
    content: '서비스가 친절했어요.',
    createdAt: '2026-03-07T10:05:00.000000',
    updatedAt: '2026-03-07T10:05:00.000000',
    images: [{ imageId: 'img-12', imageUrl: 'https://s3.cloud/test/cafe12.png' }],
    nickname: '서연',
  },
  {
    reviewId: 'b0c33ed0-a0e9-42f0-9044-8a9af234f009',
    rating: 4,
    content: '창가 자리 채광이 좋아요.',
    createdAt: '2026-03-06T09:45:00.000000',
    updatedAt: '2026-03-06T09:45:00.000000',
    images: [],
    nickname: '지우',
  },
];

export const reviewHandlers = [
  http.get(`${API_BASE_URL}/api/cafes/:cafeId/reviews`, ({ request, params }) => {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get('page') ?? '0');
    const size = Number(url.searchParams.get('size') ?? '10');
    const cafeId = String(params.cafeId ?? 'unknown-cafe');

    const content = reviewSeed.map((review) => ({
      ...review,
      reviewId: `${cafeId}-${review.reviewId}`,
    }));

    const startIndex = page * size;
    const endIndex = startIndex + size;
    const slicedContent = content.slice(startIndex, endIndex);
    const isLast = endIndex >= content.length;

    return HttpResponse.json(
      {
        status: 'success',
        code: '200',
        message: '요청이 성공적으로 처리되었습니다.',
        data: {
          content: slicedContent,
          pageable: {
            pageNumber: page,
            pageSize: size,
            sort: {
              empty: false,
              sorted: true,
              unsorted: false,
            },
            offset: startIndex,
            paged: true,
            unpaged: false,
          },
          size,
          number: page,
          sort: {
            empty: false,
            sorted: true,
            unsorted: false,
          },
          first: page === 0,
          last: isLast,
          numberOfElements: slicedContent.length,
          empty: slicedContent.length === 0,
        },
      },
      { status: 200 }
    );
  }),
];
