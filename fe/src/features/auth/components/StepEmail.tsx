// "use client";

// import { useState } from "react";
// import Image from "next/image";
// import { Input } from "@/common/components/Input";
// import Button from "@/common/components/Button";
// import { SignupStepProps } from "../types";
// import { SignupStepProps } from "../types";

// export default function StepEmail({ next, updateData }: SignupStepProps) {
//   const [email, setEmail] = useState("");
//   const [authCode, setAuthCode] = useState("");
//   const [isEmailSent, setIsEmailSent] = useState(false);
//   const [emailError, setEmailError] = useState("");
//   const [authError, setAuthError] = useState("");

//   const handleSendCode = () => {
//     if (!email.includes("@")) {
//       setEmailError("올바른 이메일 형식이 아닙니다.");
//       return;
//     }
//     setEmailError("");
//     setIsEmailSent(true);
//     alert("인증번호가 발송되었습니다. (테스트 번호: 1234)");
//   };

//   // 1. [수정] 확인 버튼 클릭 시 에러만 체크하는 함수
//   const handleCheckAuthOnly = () => {
//     if (authCode !== "1234") {
//       setAuthError("인증번호가 일치하지 않습니다.");
//     } else {
//       setAuthError("인증번호가 확인되었습니다.");
//     }
//   };

//   // 2. [추가] 하단 '다음' 버튼 클릭 시 실행될 함수 (누락되었던 부분)
//   const handleVerifyAndNext = () => {
//     if (authCode === "1234") {
//       updateData({ email });
//       next();
//     } else {
//       setAuthError("인증번호가 일치하지 않습니다.");
//     }
//   };

//   return (
//     <div className="flex flex-col h-full">
//       {/* 상단 Step 표시 */}
//       <div className="flex justify-center gap-2 mt-4 mb-10">
//         <div className="w-1.5 h-1.5 rounded-full bg-black" />
//         <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
//         <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
//       </div>

//       {/* 로고 영역 */}
//       <div className="flex flex-col items-center mb-12">
//         <Image src="/images/common/logo.png" alt="Logo" width={80} height={80} className="object-contain" />
//       </div>

//       {/* 입력 폼 영역 */}
//       <div className="flex-1">
//         <div className="h-[94px]">
//           <Input
//             label="이메일"
//             placeholder="이메일 주소를 입력해 주세요."
//             value={email}
//             onChange={(e) => {
//               setEmail(e.target.value);
//               setEmailError("");
//             }}
//             error={emailError}
//             rightElement={
//               <Button 
//                 variant="gray" 
//                 size="sm" 
//                 onClick={handleSendCode} 
//                 disabled={!email}
//                 className="w-[84px]"
//               >
//                 이메일 인증
//               </Button>
//             }
//           />
//         </div>

//         <div className="h-[94px] mt-4">
//           <Input
//             label="인증코드"
//             placeholder="인증코드를 입력해 주세요."
//             value={authCode}
//             onChange={(e) => {
//               setAuthCode(e.target.value);
//               setAuthError(""); // 1. 타이핑 시 에러 초기화 (이메일과 통일)
//             }}
//             error={authError} // 2. 이 state가 Input 내부의 <p> 태그 등에 잘 전달되는지 확인
//             rightElement={
//               <Button 
//                 variant="gray" 
//                 size="sm" 
//                 onClick={handleCheckAuthOnly}
//                 disabled={!isEmailSent || !authCode}
//                 className="w-[60px]"
//               >
//                 확인
//               </Button>
//             }
//           />
//         </div>
//       </div>

//       {/* 하단 다음 버튼 */}
//       <div className="pb-4 mt-44">
//         <Button
//           variant="gray"
//           size="full"
//           disabled={!isEmailSent || !authCode}
//           onClick={handleVerifyAndNext} // 다음 버튼은 검증 후 페이지 이동!
//           className={isEmailSent && authCode ? "!bg-[#C3304F] !text-white" : ""}
//         >
//           다음
//         </Button>
//       </div>
//     </div>
//   );
// }

// 나중에 위 코드로 대체하기

"use client";

import { useState } from "react";
import Image from "next/image";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import { SignupStepProps } from "../types";

export default function StepEmail({ next, updateData }: SignupStepProps) {
  const [email, setEmail] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [isEmailSent, setIsEmailSent] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [authError, setAuthError] = useState("");

  const handleSendCode = () => {
    if (!email.includes("@")) {
      setEmailError("올바른 이메일 형식이 아닙니다.");
      return;
    }
    setEmailError("");
    setIsEmailSent(true);
    alert("인증번호가 발송되었습니다. (테스트 번호: 1234)");
  };

  const handleCheckAuthOnly = () => {
    if (authCode !== "1234") {
      setAuthError("인증번호가 일치하지 않습니다.");
    } else {
      setAuthError("인증번호가 확인되었습니다.");
    }
  };

  // [나중에 복구] 1. 이 함수 전체의 주석을 풀고 하단 버튼 onClick에 연결하세요.
  const handleVerifyAndNext = () => {
    if (authCode === "1234") {
      updateData({ email });
      next();
    } else {
      setAuthError("인증번호가 일치하지 않습니다.");
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* 상단 Step 표시 */}
      <div className="flex justify-center gap-2 mt-4 mb-10">
        <div className="w-1.5 h-1.5 rounded-full bg-black" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
        <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
      </div>

      {/* 로고 영역 */}
      <div className="flex flex-col items-center mb-12">
        <Image src="/images/common/logo.png" alt="Logo" width={120} height={120} className="object-contain" />
      </div>

      {/* 입력 폼 영역 */}
      <div className="flex-1">
        <div className="h-[94px]">
          <Input
            label="이메일"
            placeholder="이메일 주소를 입력해 주세요."
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              setEmailError("");
            }}
            error={emailError}
            rightElement={
              <Button 
                variant="gray" 
                size="sm" 
                onClick={handleSendCode} 
                disabled={!email}
                className="w-[84px]"
              >
                이메일 인증
              </Button>
            }
          />
        </div>

        <div className="h-[94px] mt-4">
          <Input
            label="인증코드"
            placeholder="인증코드를 입력해 주세요."
            value={authCode}
            onChange={(e) => {
              setAuthCode(e.target.value);
              setAuthError(""); 
            }}
            error={authError}
            rightElement={
              <Button 
                variant="gray" 
                size="sm" 
                onClick={handleCheckAuthOnly}
                // [나중에 복구] 2. disabled={!isEmailSent || !authCode}로 변경
                disabled={false} 
                className="w-[60px]"
              >
                확인
              </Button>
            }
          />
        </div>
      </div>

      {/* 하단 다음 버튼 */}
      <div className="pb-4 mt-44">
        <Button
          variant="gray"
          size="full"
          // [나중에 복구] 3. disabled={!isEmailSent || !authCode}로 변경
          disabled={false} 
          onClick={() => {
            // [나중에 복구] 4. handleVerifyAndNext()로 교체
            updateData({ email });
            next();
          }}
          // [나중에 복구] 5. className={isEmailSent && authCode ? "!bg-[#C3304F] !text-white" : ""} 로 변경
          className="!bg-[#C3304F] !text-white"
        >
          다음
        </Button>
      </div>
    </div>
  );
}