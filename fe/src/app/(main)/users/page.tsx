"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import Header from "@/common/components/Header";
import Modal from "@/common/components/Modal";
import { Input } from "@/common/components/Input";
import Button from "@/common/components/Button";
import ReviewItem from "@/features/users/components/ReviewItem";
import { UserProfile } from "@/features/users/types";
import { getUserInfo, getMyReviews, patchUsers, patchPasswordReset, deleteUsers } from "@/features/users/api/userApi";
import { postLogout } from "@/features/auth/api/loginApi";
import { AxiosError } from "axios";
import { BaseResponse } from "@/features/auth/types";

import gearWheelIcon from "@/assets/icons/gearWheelIcon.png";

const DEFAULT_PROFILE_IMAGE = "/images/auth/welcome.png";

const formatDate = (dateStr: string) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}.${m}.${d}`;
};

function ProfileEditModal({
  isOpen,
  onClose,
  onWithdraw,
  profile,
  onAlert,
}: {
  isOpen: boolean;
  onClose: () => void;
  onWithdraw: () => void;
  profile: UserProfile;
  onAlert: (title: string, message?: string) => void;
}) {
  const queryClient = useQueryClient();
  const [nickname, setNickname] = useState(profile.nickname);
  const [nicknameError, setNicknameError] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(profile.profileImageUrl || DEFAULT_PROFILE_IMAGE);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateMutation = useMutation({
    mutationFn: patchUsers,
    onSuccess: (res) => {
      // 서버 응답이 문자열 "200" 또는 숫자 200으로 올 수 있으므로 모두 처리
      if (res.code === 200 || res.code === "200") {
        queryClient.invalidateQueries({ queryKey: ["user", "me"] });
        onAlert("수정 완료", "회원 정보가 성공적으로 수정되었습니다.");
        onClose();
      } else {
        onAlert("수정 실패", res.message || "정보 수정에 실패했습니다.");
      }
    },
    onError: () => onAlert("오류", "서버 오류가 발생했습니다."),
  });

  const validateNickname = (value: string) => {
    if (value.length === 0) return false;
    const nicknameRegex = /^[a-zA-Z0-9가-힣]+$/;
    if (!nicknameRegex.test(value)) {
      setNicknameError("공백, 특수문자, 자음/모음은 사용할 수 없습니다.");
      return false;
    }
    if (value.length < 2 || value.length > 10) {
      setNicknameError("닉네임은 2~10자 사이여야 합니다.");
      return false;
    }
    setNicknameError("");
    return true;
  };

  const handleNicknameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setNickname(value);
    validateNickname(value);
  };

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
    setPreviewUrl(DEFAULT_PROFILE_IMAGE);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSave = () => {
    if (!validateNickname(nickname)) return;
    updateMutation.mutate({
      nickname,
      profileImage: selectedFile || undefined,
      profileImageUrl: !selectedFile ? (previewUrl || undefined) : undefined
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" disableBackdropClick>
      <div className="flex flex-col gap-5">
        <div className="flex justify-end">
          <button type="button" onClick={onWithdraw} className="px-3 py-1.5 rounded-lg border border-[#C3304F] text-[12px] font-medium text-[#C3304F] active:bg-red-50 transition-colors">
            탈퇴하기
          </button>
        </div>

        <div className="flex flex-col items-center gap-3">
          <div className="relative w-[88px] h-[88px] rounded-full overflow-hidden bg-[#F5F0E8]">
            <Image src={previewUrl || DEFAULT_PROFILE_IMAGE} alt="프로필" fill className="object-cover" />
          </div>
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept="image/*" className="hidden" />
          <div className="flex gap-2">
            <button type="button" onClick={() => fileInputRef.current?.click()} className="px-4 py-2 rounded-full border border-gray-300 text-[13px] text-gray-700 font-medium active:bg-gray-50">
              사진 선택
            </button>
            <button type="button" onClick={handleResetDefault} className="px-4 py-2 rounded-full border border-gray-300 text-[13px] text-gray-700 font-medium active:bg-gray-50">
              기본 이미지
            </button>
          </div>
        </div>

        <Input label="닉네임" value={nickname} onChange={handleNicknameChange} placeholder="한글/영어/숫자 2~10자" error={nicknameError} />

        <div className="flex gap-3">
          <div className="flex-1 min-w-0">
            <Input label="생년월일" value={profile.birthDate || "정보 없음"} readOnly className="bg-gray-100! border-gray-200! text-gray-400 cursor-not-allowed" />
          </div>
          <div className="w-[72px] shrink-0">
            <Input label="성별" value={profile.gender || "정보 없음"} readOnly className="bg-gray-100! border-gray-200! text-gray-400 cursor-not-allowed" />
          </div>
        </div>

        <div className="flex gap-3 mt-1">
          <Button variant="gray" size="full" onClick={onClose} className="h-[52px] rounded-xl! text-gray-700!">
            돌아가기
          </Button>
          <Button variant="primary" size="full" onClick={handleSave} disabled={updateMutation.isPending || nicknameError !== "" || nickname.length < 2} className="h-[52px] rounded-xl!">
            {updateMutation.isPending ? "수정 중..." : "확인"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function WithdrawModal({ isOpen, onClose, nickname, onAlert }: { isOpen: boolean; onClose: () => void; nickname: string; onAlert: (title: string, message?: string) => void }) {
  const router = useRouter();
  const [isSuccess, setIsSuccess] = useState(false);

  const withdrawMutation = useMutation({
    mutationFn: deleteUsers,
    onSuccess: (res) => {
      if (res.code === 200 || res.code === "200") {
        setIsSuccess(true);
      } else {
        onAlert("탈퇴 실패", res.message || "탈퇴 처리 중 오류가 발생했습니다.");
      }
    },
  });

  const handleFinalConfirm = () => {
    localStorage.clear();
    // 쿠키도 함께 정리하여 세션 만료 알림 방지
    document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    router.push("/onboarding");
  };

  return (
    <Modal isOpen={isOpen} onClose={isSuccess ? handleFinalConfirm : onClose} size="sm" disableBackdropClick>
      <div className="flex flex-col items-center gap-6 py-2">
        {isSuccess ? (
          <>
            <div className="flex flex-col items-center gap-2 text-center">
              <span className="text-4xl mb-2">🎉</span>
              <h2 className="text-[17px] font-bold text-gray-900">탈퇴가 완료되었습니다</h2>
              <p className="text-[13px] text-gray-500 font-medium">그동안 Degging을 이용해주셔서 감사합니다.</p>
            </div>
            <Button variant="primary" size="full" onClick={handleFinalConfirm} className="h-[52px] rounded-xl!">
              확인
            </Button>
          </>
        ) : (
          <>
            <div className="flex flex-col items-center gap-2 text-center">
              <h2 className="text-[17px] font-bold text-gray-900">정말 탈퇴하시겠어요?</h2>
              <p className="text-[13px] text-[#C3304F] font-medium">탈퇴 시, {nickname}님의 모든 기록이 삭제됩니다.</p>
            </div>
            <div className="flex gap-3 w-full">
              <Button variant="gray" size="full" onClick={onClose} className="h-[52px] rounded-xl! text-gray-700!">돌아가기</Button>
              <Button variant="primary" size="full" onClick={() => withdrawMutation.mutate()} disabled={withdrawMutation.isPending} className="h-[52px] rounded-xl!">
                {withdrawMutation.isPending ? "처리 중..." : "탈퇴하기"}
              </Button>
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}

function PasswordChangeModal({ isOpen, onClose, onAlert }: { isOpen: boolean; onClose: () => void; onAlert: (title: string, message?: string) => void }) {
  const [oldPw, setOldPw] = useState("");
  const [oldPwError, setOldPwError] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPwError, setNewPwError] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [confirmPwError, setConfirmPwError] = useState("");

  const PW_REGEX = /^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*]).{8,16}$/;

  const passwordMutation = useMutation({
    mutationFn: patchPasswordReset,
    onSuccess: (res) => {
      if (res.code === 200 || res.code === "200") {
        onAlert("변경 완료", "비밀번호가 성공적으로 변경되었습니다.");
        onClose();
      } else {
        onAlert("변경 실패", res.message || "비밀번호 변경에 실패했습니다.");
      }
    },
    onError: (error: AxiosError<BaseResponse<null>>) => {
      const serverMessage = error.response?.data?.message;
      onAlert("오류", serverMessage || "서버 오류가 발생했습니다. 다시 시도해주세요.");
    },
  });

  const handleNewPwChange = (val: string) => {
    setNewPw(val);
    setNewPwError(val && !PW_REGEX.test(val) ? "8~16자 이내의 영어+특수문자+숫자 조합으로 해주세요." : "");
    if (confirmPw && val !== confirmPw) setConfirmPwError("비밀번호가 일치하지 않습니다.");
    else setConfirmPwError("");
  };

  const handleSubmit = () => {
    // 프론트엔드 기본 유효성 검사
    if (!oldPw) {
      setOldPwError("현재 비밀번호를 입력해주세요.");
      return;
    }
    if (!newPw || !PW_REGEX.test(newPw)) {
      setNewPwError("새 비밀번호 형식이 올바르지 않습니다.");
      return;
    }
    if (newPw !== confirmPw) {
      setConfirmPwError("비밀번호 확인이 일치하지 않습니다.");
      return;
    }

    passwordMutation.mutate({ 
      oldPassword: oldPw, 
      newPassword: newPw, 
      confirmPassword: confirmPw 
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg" disableBackdropClick>
      <div className="flex flex-col gap-5">
        <h2 className="text-[16px] font-bold text-gray-900 mb-1">회원 비밀번호 변경</h2>
        
        <Input 
          label="현재 비밀번호 확인" 
          type="password" 
          value={oldPw} 
          onChange={(e) => { setOldPw(e.target.value); setOldPwError(""); }} 
          placeholder="현재 비밀번호를 입력하세요" 
          error={oldPwError} 
        />
        
        <Input 
          label="새로운 비밀번호" 
          type="password" 
          value={newPw} 
          onChange={(e) => handleNewPwChange(e.target.value)} 
          placeholder="8~16자 이내의 영문, 숫자, 특수문자" 
          error={newPwError} 
        />
        
        <Input 
          label="비밀번호 확인" 
          type="password" 
          value={confirmPw} 
          onChange={(e) => { setConfirmPw(e.target.value); setConfirmPwError(e.target.value !== newPw ? "비밀번호가 일치하지 않습니다." : ""); }} 
          placeholder="새 비밀번호를 다시 입력하세요" 
          error={confirmPwError} 
        />

        <div className="flex gap-3 mt-1">
          <Button variant="gray" size="full" onClick={onClose} className="h-[52px] rounded-xl! text-gray-700!">돌아가기</Button>
          <Button 
            variant="primary" 
            size="full" 
            onClick={handleSubmit} 
            disabled={passwordMutation.isPending} 
            className="h-[52px] rounded-xl!"
          >
            {passwordMutation.isPending ? "변경 중..." : "변경완료"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

function SettingsDropdown({ onClose, onEditProfile, onChangePassword, onLogout }: { onClose: () => void; onEditProfile: () => void; onChangePassword: () => void; onLogout: () => void }) {
  const menuItems = [
    { label: "내 정보 수정", onClick: () => { onEditProfile(); onClose(); }, danger: false },
    { label: "비밀번호 변경", onClick: () => { onChangePassword(); onClose(); }, danger: false },
    { label: "로그아웃", onClick: () => { onLogout(); onClose(); }, danger: true },
  ];
  return (
    <div className="w-[140px] bg-white border border-gray-200 rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.10)] overflow-hidden flex flex-col">
      {menuItems.map((item, idx) => (
        <button key={item.label} type="button" onClick={item.onClick} className={`w-full text-center px-4 py-3 text-[14px] font-medium transition-colors active:bg-gray-50 ${item.danger ? "text-[#C3304F]" : "text-gray-800"} ${idx !== menuItems.length - 1 ? "border-b border-gray-100" : ""}`}>
          {item.label}
        </button>
      ))}
    </div>
  );
}

export default function UserPage() {
  const router = useRouter();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProfileEditOpen, setIsProfileEditOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [isPasswordChangeOpen, setIsPasswordChangeOpen] = useState(false);
  
  // 알럿/컨펌용 모달 상태 (인라인 관리)
  const [dialog, setDialog] = useState<{
    isOpen: boolean;
    title: string;
    message?: string;
    type: "alert" | "confirm";
    emoji?: string;
    onConfirm?: () => void;
  }>({ isOpen: false, title: "", type: "alert" });

  const showAlert = (title: string, message?: string) => {
    setDialog({ isOpen: true, title, message, type: "alert", emoji: "💡" });
  };

  const showConfirm = (title: string, message: string, onConfirm: () => void) => {
    setDialog({ isOpen: true, title, message, type: "confirm", emoji: "❓", onConfirm });
  };

  const { data: profileData, isLoading: isProfileLoading, isError: isProfileError } = useQuery({
    queryKey: ["user", "me"],
    queryFn: getUserInfo,
    select: (res) => res.data // 매핑 로직 제거, 서버 데이터 그대로 사용
  });

  const { data: reviewsData, isLoading: isReviewsLoading } = useQuery({
    queryKey: ["user", "reviews", "top3"],
    queryFn: () => getMyReviews(0, 3),
    select: (res) => res.data?.content || []
  });

  const handleLogout = () => {
    showConfirm("로그아웃 하시겠습니까?", "", async () => {
      await postLogout();
    });
  };

  if (isProfileLoading) return <div className="flex items-center justify-center h-screen text-gray-400">로딩 중...</div>;
  if (isProfileError || !profileData) return <div className="flex items-center justify-center h-screen text-red-400">데이터를 불러오지 못했습니다.</div>;

  return (
    <div className="flex flex-col min-h-full bg-bg_white font-pretendard overflow-x-hidden">
      <div className="relative">
        <Header centerContent="마이페이지" rightContent={<button type="button" onClick={() => setIsSettingsOpen((prev) => !prev)} className="p-1 active:opacity-50 transition-opacity"><Image src={gearWheelIcon} alt="설정" width={22} height={22} /></button>} />
      
      {/* 팝업용 공통 모달 UI (Button과 Modal 컴포넌트 조합) */}
      <Modal isOpen={dialog.isOpen} onClose={() => setDialog(prev => ({ ...prev, isOpen: false }))} size="sm">
        <div className="flex flex-col items-center gap-6 py-2">
          <div className="flex flex-col items-center gap-2 text-center">
            {dialog.emoji && <span className="text-4xl mb-2">{dialog.emoji}</span>}
            <h2 className="text-[16px] font-bold text-gray-900 leading-snug whitespace-pre-wrap break-keep">{dialog.title}</h2>
            {dialog.message && (
              <p className="text-[13px] text-gray-500 font-medium leading-relaxed">{dialog.message}</p>
            )}
          </div>
          <div className="flex gap-3 w-full">
            {dialog.type === "confirm" && (
              <Button variant="gray" size="full" onClick={() => setDialog(prev => ({ ...prev, isOpen: false }))} className="h-[52px] rounded-xl! text-gray-700!">
                취소
              </Button>
            )}
            <Button 
              variant="primary" 
              size="full" 
              onClick={() => { dialog.onConfirm?.(); setDialog(prev => ({ ...prev, isOpen: false })); }} 
              className="h-[52px] rounded-xl!"
            >
              확인
            </Button>
          </div>
        </div>
      </Modal>

      {isSettingsOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsSettingsOpen(false)} />
            <div className="absolute right-4 top-14 z-50">
              <SettingsDropdown onClose={() => setIsSettingsOpen(false)} onEditProfile={() => setIsProfileEditOpen(true)} onChangePassword={() => setIsPasswordChangeOpen(true)} onLogout={handleLogout} />
            </div>
          </>
        )}
      </div>

      <div className="flex flex-col gap-4 px-5 pt-5 pb-24">
        <div className="bg-white rounded-[20px] border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-4 mb-5">
            <div className="relative w-[68px] h-[68px] rounded-full overflow-hidden bg-[#F5F0E8] shrink-0">
              <Image src={profileData.profileImageUrl || DEFAULT_PROFILE_IMAGE} alt="프로필" fill className="object-cover" />
            </div>
            <div className="flex flex-col gap-1 min-w-0">
              <p className="text-[17px] font-bold text-gray-900 truncate">{profileData.nickname}님</p>
              <p className="text-[13px] text-gray-500 truncate">{profileData.email}</p>
            </div>
          </div>
          <div className="border-t border-dashed border-gray-200 mb-4" />
          <div className="flex flex-col gap-2">
            <p className="text-[14px] font-semibold text-gray-700">{profileData.nickname}님이 자주 보는 해시태그</p>
            <div className="flex flex-wrap gap-2">
              {profileData.preferredTags?.map((tag) => (
                <span key={tag} className="px-3 py-1.5 rounded-full border border-[#C6964D] text-[13px] text-[#C6964D] font-medium bg-[#FFF9F0]">#{tag}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-[16px] font-bold text-gray-900">내가 쓴 리뷰</h2>
            <button type="button" onClick={() => router.push("/users/reviews")} className="px-3 py-1.5 rounded-[8px] border border-gray-200 text-[12px] font-medium text-gray-600 bg-white active:bg-gray-50">전체보기</button>
          </div>
          <div className="flex flex-col gap-2">
            {isReviewsLoading ? (
               <div className="py-10 text-center text-gray-400 text-[13px]">리뷰를 불러오는 중입니다...</div>
            ) : reviewsData && reviewsData.length > 0 ? (
              reviewsData.map((review) => (
                <ReviewItem 
                  key={review.reviewId} 
                  reviewId={review.reviewId}
                  cafeName={review.cafeName}
                  cafeImageUrl={review.thumbnailImage || "/images/cafe/baseCafeImage.png"}
                  content={review.content}
                  createdAt={formatDate(review.createdAt)}
                />
              ))
            ) : (
              <div className="bg-white rounded-2xl p-8 text-center border border-dashed border-gray-200">
                 <p className="text-gray-400 text-[13px]">아직 작성한 리뷰가 없습니다.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {isProfileEditOpen && <ProfileEditModal isOpen={isProfileEditOpen} onClose={() => setIsProfileEditOpen(false)} onWithdraw={() => { setIsProfileEditOpen(false); setIsWithdrawOpen(true); }} profile={profileData} onAlert={showAlert} />}
      {isWithdrawOpen && <WithdrawModal isOpen={isWithdrawOpen} onClose={() => setIsWithdrawOpen(false)} nickname={profileData.nickname} onAlert={showAlert} />}
      {isPasswordChangeOpen && <PasswordChangeModal isOpen={isPasswordChangeOpen} onClose={() => setIsPasswordChangeOpen(false)} onAlert={showAlert} />}
    </div>
  );
}
