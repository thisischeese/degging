"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

import Header from "@/common/components/Header";
import Modal from "@/common/components/Modal";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import ReviewItem from "@/features/users/components/ReviewItem";
import { UserProfile, ReviewItem as ReviewItemType } from "@/features/users/types";

import gearWheelIcon from "@/assets/icons/gearWheelIcon.png";

// ─────────────────────────────────────────────────────────
// Mock 데이터 (API 연동 전 임시)
// ─────────────────────────────────────────────────────────
const MOCK_PROFILE: UserProfile = {
  userId: 1,
  nickname: "oo",
  email: "ssaffy@ssafy.com",
  profileImageUrl: "/images/auth/welcome.png",
  topHashtags: ["#차분한", "#힙한", "#따뜻한"],
  birthDate: "1999.02.12",
  gender: "여",
};

const MOCK_REVIEWS: ReviewItemType[] = [
  { reviewId: 1, cafeId: 1, cafeName: "서울 신라 호텔", cafeImageUrl: "/images/curation/mangoBingsu.png", content: "하 진짜 너무 맛있었음 친구들이랑 총 3명이서 왔는데 5개....", createdAt: "2026.03.04" },
  { reviewId: 2, cafeId: 2, cafeName: "서울 신라 호텔", cafeImageUrl: "/images/curation/mangoBingsu.png", content: "하 진짜 너무 맛있었음 친구들이랑 총 3명이서 왔는데 5개....", createdAt: "2026.03.04" },
  { reviewId: 3, cafeId: 3, cafeName: "서울 신라 호텔", cafeImageUrl: "/images/curation/mangoBingsu.png", content: "하 진짜 너무 맛있었음 친구들이랑 총 3명이서 왔는데 5개....", createdAt: "2026.03.04" },
  { reviewId: 4, cafeId: 4, cafeName: "서울 신라 호텔", cafeImageUrl: "/images/curation/mangoBingsu.png", content: "하 진짜 너무 맛있었음 친구들이랑 총 3명이서 왔는데 5개....", createdAt: "2026.03.04" },
  { reviewId: 5, cafeId: 5, cafeName: "서울 신라 호텔", cafeImageUrl: "/images/curation/mangoBingsu.png", content: "하 진짜 너무 맛있었음 친구들이랑 총 3명이서 왔는데 5개....", createdAt: "2026.03.04" },
];

// ─────────────────────────────────────────────────────────
// 프로필 수정 모달
// ─────────────────────────────────────────────────────────
function ProfileEditModal({
  isOpen,
  onClose,
  onWithdraw,
  profile,
  onUpdate,
}: {
  isOpen: boolean;
  onClose: () => void;
  onWithdraw: () => void;
  profile: UserProfile;
  onUpdate: (newNickname: string, newImageUrl: string | null) => void;
}) {
  const [nickname, setNickname] = useState(profile.nickname);
  const [previewUrl, setPreviewUrl] = useState<string | null>(profile.profileImageUrl || "/images/auth/welcome.png");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleResetDefault = () => {
    setSelectedFile(null);
    setPreviewUrl("/images/auth/welcome.png");
    // input file 초기화 (같은 파일을 다시 선택할 수 있게)
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleSave = () => {
    // TODO: PATCH /api/users 연동 (multipart/form-data 사용)
    // 실제 서버 연동 전까지는 previewUrl을 그대로 상태에 반영하여 UI 연결
    onUpdate(nickname, previewUrl);
    console.log("Saving changes:", { nickname, selectedFile, previewUrl });
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" disableBackdropClick>
      <div className="flex flex-col gap-5">
        {/* 상단: 탈퇴하기 버튼 */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onWithdraw}
            className="px-3 py-1.5 rounded-lg border border-[#C3304F] text-[12px] font-medium text-[#C3304F] active:bg-red-50 transition-colors"
          >
            탈퇴하기
          </button>
        </div>

        {/* 프로필 이미지 */}
        <div className="flex flex-col items-center gap-3">
          <div className="relative w-[88px] h-[88px] rounded-full overflow-hidden bg-[#F5F0E8]">
            <Image
              src={previewUrl || "/images/auth/welcome.png"}
              alt="프로필"
              fill
              className="object-cover"
            />
          </div>
          
          {/* 숨겨진 파일 입풋 */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept="image/*"
            className="hidden"
          />

          {/* 사진 선택 / 기본 이미지 버튼 */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={triggerFileInput}
              className="px-4 py-2 rounded-full border border-gray-300 text-[13px] text-gray-700 font-medium active:bg-gray-50 transition-colors"
            >
              사진 선택
            </button>
            <button
              type="button"
              onClick={handleResetDefault}
              className="px-4 py-2 rounded-full border border-gray-300 text-[13px] text-gray-700 font-medium active:bg-gray-50 transition-colors"
            >
              기본 이미지
            </button>
          </div>
        </div>

        {/* 닉네임 입력 */}
        <Input
          label="닉네임"
          value={nickname}
          onChange={(e) => setNickname((e.target as HTMLInputElement).value)}
          placeholder="닉네임을 입력하세요"
        />

        {/* 생년월일 + 성별 (읽기 전용 - 수정 불가)
            wrapper div로 너비를 제어해야 Input 내부의 w-full과 충돌하지 않음 */}
        <div className="flex gap-3">
          {/* 생년월일: 남은 공간 전부 차지 */}
          <div className="flex-1 min-w-0">
            <Input
              label="생년월일"
              value={profile.birthDate || "정보 없음"}
              readOnly
              className="bg-gray-100! border-gray-200! text-gray-400 cursor-not-allowed"
            />
          </div>
          {/* 성별: 고정 너비 72px */}
          <div className="w-[72px] shrink-0">
            <Input
              label="성별"
              value={profile.gender || "정보 없음"}
              readOnly
              className="bg-gray-100! border-gray-200! text-gray-400 cursor-not-allowed"
            />
          </div>
        </div>


        {/* 저장 버튼 */}
        <Button
          variant="primary"
          size="full"
          onClick={handleSave}
          className="mt-1 h-[52px] rounded-xl!"
        >
          저장
        </Button>
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────────────────
// 탈퇴 확인 모달
// ─────────────────────────────────────────────────────────
function WithdrawModal({
  isOpen,
  onClose,
  nickname,
}: {
  isOpen: boolean;
  onClose: () => void;
  nickname: string;
}) {
  const router = useRouter();

  const handleWithdraw = () => {
    // TODO: DELETE /api/users 연동
    router.push("/login");
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm" disableBackdropClick>
      <div className="flex flex-col items-center gap-6 py-2">
        {/* 제목 & 경고 메세지 */}
        <div className="flex flex-col items-center gap-2 text-center">
          <h2 className="text-[17px] font-bold text-gray-900">정말 탈퇴하시겠어요?</h2>
          <p className="text-[13px] text-[#C3304F] font-medium">
            탈퇴 시, {nickname}님의 모든 기록이 삭제됩니다.
          </p>
        </div>

        {/* 버튼 */}
        <div className="flex gap-3 w-full">
          <Button
            variant="gray"
            size="full"
            onClick={onClose}
            className="h-[52px] rounded-xl! text-gray-700!"
          >
            돌아가기
          </Button>
          <Button
            variant="primary"
            size="full"
            onClick={handleWithdraw}
            className="h-[52px] rounded-xl!"
          >
            탈퇴하기
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────────────────
// 비밀번호 변경 모달
// ─────────────────────────────────────────────────────────
function PasswordChangeModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [currentPw, setCurrentPw] = useState("");
  const [currentPwError, setCurrentPwError] = useState("");
  const [currentPwVerified, setCurrentPwVerified] = useState(false);

  const [newPw, setNewPw] = useState("");
  const [newPwError, setNewPwError] = useState("");

  const [confirmPw, setConfirmPw] = useState("");
  const [confirmPwError, setConfirmPwError] = useState("");

  // 비밀번호 정규식: 8~16자, 영문+특수문자+숫자 조합
  const PW_REGEX = /^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).{8,16}$/;

  const handleVerifyCurrentPw = () => {
    if (!currentPw) {
      setCurrentPwError("비밀번호를 입력해주세요.");
      return;
    }
    // TODO: API로 현재 비밀번호 검증
    // 임시: 아무 입력이나 통과 처리
    setCurrentPwError("");
    setCurrentPwVerified(true);
  };

  const handleNewPwChange = (val: string) => {
    setNewPw(val);
    if (val && !PW_REGEX.test(val)) {
      setNewPwError("8~16자 이내의 영어 + 특수문자+숫자 조합으로 해주세요.");
    } else {
      setNewPwError("");
    }
    // 확인 비밀번호도 재검사
    if (confirmPw && val !== confirmPw) {
      setConfirmPwError("비밀번호가 일치하지 않습니다.");
    } else if (confirmPw) {
      setConfirmPwError("");
    }
  };

  const handleConfirmPwChange = (val: string) => {
    setConfirmPw(val);
    if (val && val !== newPw) {
      setConfirmPwError("비밀번호가 일치하지 않습니다.");
    } else {
      setConfirmPwError("");
    }
  };

  const handleSubmit = () => {
    let hasError = false;
    if (!currentPwVerified) {
      setCurrentPwError("현재 비밀번호를 먼저 확인해주세요.");
      hasError = true;
    }
    if (!newPw) {
      setNewPwError("새 비밀번호를 입력해주세요.");
      hasError = true;
    } else if (!PW_REGEX.test(newPw)) {
      setNewPwError("8~16자 이내의 영어 + 특수문자+숫자 조합으로 해주세요.");
      hasError = true;
    }
    if (!confirmPw) {
      setConfirmPwError("비밀번호 확인을 입력해주세요.");
      hasError = true;
    } else if (newPw !== confirmPw) {
      setConfirmPwError("비밀번호가 일치하지 않습니다.");
      hasError = true;
    }
    if (hasError) return;
    // TODO: PATCH /api/users/password 연동
    onClose();
  };

  const handleClose = () => {
    // 닫을 때 상태 초기화
    setCurrentPw(""); setCurrentPwError(""); setCurrentPwVerified(false);
    setNewPw(""); setNewPwError("");
    setConfirmPw(""); setConfirmPwError("");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} size="lg" disableBackdropClick>
      <div className="flex flex-col gap-5">
        <h2 className="text-[16px] font-bold text-gray-900 mb-1">회원 비밀번호 변경</h2>

        {/* 현재 비밀번호 확인 */}
        <Input
          label="현재 비밀번호 확인"
          type="password"
          value={currentPw}
          onChange={(e) => {
            setCurrentPw((e.target as HTMLInputElement).value);
            setCurrentPwError("");
            setCurrentPwVerified(false);
          }}
          placeholder="비밀번호를 입력하세요"
          error={currentPwError}
          disabled={currentPwVerified} // 확인 성공 시 수정 불가
          rightElement={
            <button
              type="button"
              onClick={handleVerifyCurrentPw}
              disabled={currentPwVerified}
              className={`px-4 py-2 rounded-full text-[13px] font-semibold whitespace-nowrap transition-opacity
                ${currentPwVerified ? "bg-green-500 text-white cursor-not-allowed" : "bg-[#C3304F] text-white active:opacity-80"}
              `}
            >
              {currentPwVerified ? "확인됨" : "확인"}
            </button>
          }
        />
        {/* 확인 완료 후 안내 메세지 */}
        {currentPwVerified && (
          <p className="text-[12px] text-green-600 px-1 -mt-3">✅ 비밀번호가 확인되었습니다.</p>
        )}

        {/* 새로운 비밀번호 */}
        <Input
          label="새로운 비밀번호"
          type="password"
          value={newPw}
          onChange={(e) => handleNewPwChange((e.target as HTMLInputElement).value)}
          placeholder="8~16자 이내의 영문, 숫자, 특수문자"
          error={newPwError}
          disabled={!currentPwVerified} // 기존 비밀번호 확인 전까지 비활성화
        />

        {/* 비밀번호 확인 */}
        <Input
          label="비밀번호 확인"
          type="password"
          value={confirmPw}
          onChange={(e) => handleConfirmPwChange((e.target as HTMLInputElement).value)}
          placeholder="새로운 비밀번호를 다시 입력하세요"
          error={confirmPwError}
          disabled={!currentPwVerified} // 기존 비밀번호 확인 전까지 비활성화
        />

        {/* 하단 버튼 */}
        <div className="flex gap-3 mt-1">
          <Button
            variant="gray"
            size="full"
            onClick={handleClose}
            className="h-[52px] rounded-xl! text-gray-700!"
          >
            돌아가기
          </Button>
          <Button
            variant="primary"
            size="full"
            onClick={handleSubmit}
            className="h-[52px] rounded-xl!"
          >
            변경완료
          </Button>
        </div>
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────────────────
// 설정 드롭다운 컴포넌트
// ─────────────────────────────────────────────────────────
function SettingsDropdown({
  onClose,
  onEditProfile,
  onChangePassword,
  onLogout,
}: {
  onClose: () => void;
  onEditProfile: () => void;
  onChangePassword: () => void;
  onLogout: () => void;
}) {
  const menuItems = [
    { label: "내 정보 수정", onClick: () => { onEditProfile(); onClose(); }, danger: false },
    { label: "비밀번호 변경", onClick: () => { onChangePassword(); onClose(); }, danger: false },
    { label: "로그아웃", onClick: () => { onLogout(); onClose(); }, danger: true },
  ];

  return (
    <div className="w-[140px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.10)] overflow-hidden flex flex-col">
      {menuItems.map((item, idx) => (
        <button
          key={item.label}
          type="button"
          onClick={item.onClick}
          className={`w-full text-center px-4 py-3 text-[14px] font-medium transition-colors active:bg-gray-50
            ${item.danger ? "text-[#C3304F]" : "text-gray-800"}
            ${idx !== menuItems.length - 1 ? "border-b border-gray-100" : ""}
          `}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}

import { useEffect } from "react";
import { getUserInfo } from "@/features/users/api/userApi";

// 메인 마이페이지
export default function UserPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  // 모달 상태
  const [isProfileEditOpen, setIsProfileEditOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [isPasswordChangeOpen, setIsPasswordChangeOpen] = useState(false);

  // 프로필 데이터 상태 관리 (초기값은 API에서 받아올 때까지 null 또는 MOCK_PROFILE 등 활용 가능)
  // 여기서는 API 로딩 화면을 보여주기 위해 null을 사용할 수도 있지만, 기존 에러를 방지하기 위해 일단 MOCK_PROFILE을 넣고 바로 덮어씁니다.
  const [profile, setProfile] = useState<UserProfile>(MOCK_PROFILE);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const result = await getUserInfo() as unknown as { code: number; data: Record<string, unknown> };
        if (result.code === 200) {
          // MSW에서 오는 데이터(result.data)를 UserProfile 규격에 맞게 변환하거나 그대로 덮어씁니다.
          // 현재 MSW 데이터는 { id: 1, email: "user...", name: "김다희", nickname: "와아앙", profileImgUrl: "...", tags: [...], reviewCount: 15 } 입니다.
          const apiData = result.data;
          setProfile({
            userId: Number(apiData.id),
            nickname: String(apiData.nickname),
            email: String(apiData.email),
            profileImageUrl: String(apiData.profileImgUrl),
            topHashtags: Array.isArray(apiData.tags) ? apiData.tags.map((tag: unknown) => `#${String(tag)}`) : [],
            birthDate: "정보 없음", // MSW 데이터에 없으므로 기본값
            gender: "정보 없음",   // MSW 데이터에 전송되지 않으므로 기본값
          });
        }
      } catch (error) {
        console.error("유저 정보 불러오기 실패:", error);
      }
    };

    fetchUserProfile();
  }, []);

  const handleUpdateProfile = (newNickname: string, newImageUrl: string | null) => {
    setProfile(prev => ({
      ...prev,
      nickname: newNickname,
      profileImageUrl: newImageUrl
    }));
  };

  const previewReviews = MOCK_REVIEWS.slice(0, 5);

  const handleLogout = () => {
    // TODO: 로그아웃 API 연동
    router.push("/login");
  };

  const handleWithdrawClick = () => {
    setIsProfileEditOpen(false);
    setIsWithdrawOpen(true);
  };

  return (
    <div className="flex flex-col min-h-full bg-bg_white font-pretendard overflow-x-hidden">

      {/* ── 헤더 ── */}
      <div className="relative">
        <Header
          centerContent="마이페이지"
          rightContent={
            <button
              type="button"
              onClick={() => setIsSettingsOpen((prev) => !prev)}
              className="p-1 active:opacity-50 transition-opacity"
            >
              <Image
                src={gearWheelIcon}
                alt="설정"
                width={22}
                height={22}
                className="object-contain"
              />
            </button>
          }
        />
        {/* 설정 드롭다운 */}
        {isSettingsOpen && (
          <>
            {/* 바깥 클릭 닫기용 투명 오버레이 */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsSettingsOpen(false)}
            />
            <div className="absolute right-4 top-14 z-50">
              <SettingsDropdown
                onClose={() => setIsSettingsOpen(false)}
                onEditProfile={() => setIsProfileEditOpen(true)}
                onChangePassword={() => setIsPasswordChangeOpen(true)}
                onLogout={handleLogout}
              />
            </div>
          </>
        )}
      </div>

      {/* ── 콘텐츠 ── */}
      <div className="flex flex-col gap-4 px-5 pt-5 pb-24">

        {/* 1. 프로필 카드 */}
        <div className="bg-white rounded-[20px] border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-4 mb-5">
            <div className="relative w-[68px] h-[68px] rounded-full overflow-hidden bg-[#F5F0E8] shrink-0">
              <Image
                src={profile.profileImageUrl ?? "/images/auth/welcome.png"}
                alt="프로필"
                fill
                className="object-cover"
              />
            </div>
            <div className="flex flex-col gap-1 min-w-0">
              <p className="text-[17px] font-bold text-gray-900 truncate">
                {profile.nickname}님
              </p>
              <p className="text-[13px] text-gray-500 truncate">
                {profile.email}
              </p>
            </div>
          </div>

          <div className="border-t border-dashed border-gray-200 mb-4" />

          <div className="flex flex-col gap-2">
            <p className="text-[14px] font-semibold text-gray-700">
              {profile.nickname}님이 자주 보는 해시태그
            </p>
            <div className="flex flex-wrap gap-2">
              {profile.topHashtags.map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 rounded-full border border-[#C6964D] text-[13px] text-[#C6964D] font-medium bg-[#FFF9F0]"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* 2. 리뷰 섹션 */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-[16px] font-bold text-gray-900">내가 쓴 리뷰</h2>
            <button
              type="button"
              onClick={() => router.push("/users/reviews")}
              className="px-3 py-1.5 rounded-[8px] border border-gray-200 text-[12px] font-medium text-gray-600 bg-white active:bg-gray-50 transition-colors"
            >
              전체보기
            </button>
          </div>

          <div className="flex flex-col gap-2">
            {previewReviews.length > 0 ? (
              previewReviews.map((review) => (
                <ReviewItem key={review.reviewId} {...review} />
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                <p className="text-[14px]">아직 작성한 리뷰가 없습니다.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── 모달들 (조건부 렌더링으로 닫힐 때마다 모든 데이터 완벽하게 리셋!) ── */}
      {isProfileEditOpen && (
        <ProfileEditModal
          isOpen={isProfileEditOpen}
          onClose={() => setIsProfileEditOpen(false)}
          onWithdraw={handleWithdrawClick}
          profile={profile}
          onUpdate={handleUpdateProfile}
        />
      )}
      {isWithdrawOpen && (
        <WithdrawModal
          isOpen={isWithdrawOpen}
          onClose={() => setIsWithdrawOpen(false)}
          nickname={profile.nickname}
        />
      )}
      {isPasswordChangeOpen && (
        <PasswordChangeModal
          isOpen={isPasswordChangeOpen}
          onClose={() => setIsPasswordChangeOpen(false)}
        />
      )}
    </div>
  );
}
