# 1. Build Stage
FROM gradle:jdk21-jammy AS builder
WORKDIR /app

# 빌드 설정 파일만 먼저 복사
COPY gradlew .
COPY gradle gradle
COPY build.gradle settings.gradle ./

# 의존성 미리 다운로드
RUN chmod +x ./gradlew
RUN ./gradlew dependencies --no-daemon

# 주의. docker-compose.yml context 설정 be로 지정
# 소스 코드 전체 복사 후 빌드
COPY . .
RUN ./gradlew clean bootJar -x test --no-daemon

# 2. Run Stage
FROM eclipse-temurin:21-jre-jammy
WORKDIR /app

# plain.jar 제외한 실행용 jar만 가져옴
# 실행에 불필요한 JDK 대신 가벼운 JRE 버전 사용 (이미지 용량 절감)
# 빌드 스테이지에서 생성된 실행 가능한 jar만 복사
COPY --from=builder /app/build/libs/*-SNAPSHOT.jar app.jar

# 환경 변수 설정
ENV TZ=Asia/Seoul

# Spring Boot 프로파일 설정이 필요하다면 아래 주석 해제 후 수정
# ENV SPRING_PROFILES_ACTIVE=prod

# 한국 시간 설정 적용
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 8080

# 컨테이너 뜨자마자 java -jar app.jar 명령어 강제 실행
# 컨테이너가 exe처럼 동작하도록
ENTRYPOINT ["java", "-jar", "app.jar"]
