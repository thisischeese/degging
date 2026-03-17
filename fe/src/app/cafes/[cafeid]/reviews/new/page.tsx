'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Camera, ArrowLeft, Star } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/common/components/Input';
import Button from '@/common/components/Button';
import Image from 'next/image';

export default function ReviewCreatePage() {
    const params = useParams();
    const router = useRouter();
    const cafeid = params.cafeid as string;

    const [rating, setRating] = useState<number>(0);
    const [content, setContent] = useState<string>('');
    const [images, setImages] = useState<File[]>([]);
    const [previewUrls, setPreviewUrls] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isOverLimit, setIsOverLimit] = useState(false);

    const fileInputRef = useRef<HTMLInputElement>(null);
    const starContainerRef = useRef<HTMLDivElement>(null);

    // 미리보기 URL 해제
    useEffect(() => {
        return () => {
            previewUrls.forEach(url => URL.revokeObjectURL(url));
        };
    }, [previewUrls]);

    const handleBack = () => {
        router.back();
    };

    const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const fileArray = Array.from(e.target.files);
            const totalImages = images.length + fileArray.length;
            
            if (totalImages > 3) {
                // 이미지가 3개를 초과하면 안내 문구를 표시하고 추가하지 않음
                // 빈 반환값은 파일 업로드를 방지함
                setIsOverLimit(true);
            } else {
                setIsOverLimit(false);
                setImages(prev => [...prev, ...fileArray]);
                const urls = fileArray.map(file => URL.createObjectURL(file));
                setPreviewUrls(prev => [...prev, ...urls]);
            }
        }
        // 필요한 경우 동일한 파일을 다시 선택할 수 있도록 파일 입력값 초기화
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const removeImage = (indexToRemove: number) => {
        setImages(prev => prev.filter((_, index) => index !== indexToRemove));
        setPreviewUrls(prev => {
            const newUrls = [...prev];
            URL.revokeObjectURL(newUrls[indexToRemove]);
            newUrls.splice(indexToRemove, 1);
            return newUrls;
        });
    };

    const handleStarPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
        if (!starContainerRef.current) return;

        const rect = starContainerRef.current.getBoundingClientRect();
        // 별 컨테이너 내의 상대적인 마우스 위치 계산
        // 전체 너비는 약 별 5개 + 간격(4개)입니다. 별 인덱스별로 계산합니다.
        const gap = 4; // gap-1은 4px입니다.
        const starWidth = 32; // w-[32px]는 32px입니다.

        let newRating = 0;
        const x = e.clientX - rect.left;

        for (let i = 0; i < 5; i++) {
            const starStart = i * (starWidth + gap);
            const starEnd = starStart + starWidth;

            if (x >= starStart && x <= starEnd) {
                const relativeX = x - starStart;
                if (relativeX < starWidth / 2) {
                    newRating = i + 0.5;
                } else {
                    newRating = i + 1;
                }
                break;
            } else if (i < 4 && x > starEnd && x < starEnd + gap) {
                // 간격 클릭 시, 이전 별이 가득 찬 것으로 간주
                newRating = i + 1;
                break;
            } else if (x > starEnd) {
                newRating = i + 1; // 이 별을 지남
            }
        }

        if (newRating > 0) {
            setRating(newRating);
        }
    };

    // 별 위에서 포인터 드래그 허용
    const handleStarPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
        if (e.buttons !== 1) return; // 마우스 버튼을 누르고 있는 동안에만 트리거
        handleStarPointerDown(e);
    };

    const handleSubmit = async () => {
        try {
            setIsSubmitting(true);
            const formData = new FormData();
            formData.append('rating', rating.toString());
            formData.append('content', content);
            images.forEach(image => {
                formData.append('images', image);
            });

            // 여기서 formData와 함께 API 호출이 이루어지는 것으로 가정
            // 예시: await fetch(`/api/cafes/${cafeid}/reviews`, { method: 'POST', body: formData })
            console.log('Sending Review Data:', {
                rating,
                content,
                imageCount: images.length
            });

            // localStorage에 저장하기 위해 이미지를 base64로 읽기
            let base64Image = '/images/cafe/cafe1.png'; // 기본값
            if (images.length > 0) {
                const fileReader = new FileReader();
                const file = images[0];

                const base64Promise = new Promise<string>((resolve) => {
                    fileReader.onload = () => resolve(fileReader.result as string);
                    fileReader.onerror = () => resolve('/images/cafe/cafe1.png');
                });
                fileReader.readAsDataURL(file);
                base64Image = await base64Promise;
            }

            const newReview = {
                id: `local-${Date.now()}`,
                rating,
                content,
                imageUrl: base64Image,
                timestamp: Date.now()
            };

            // localStorage에 저장
            const existingReviewsStr = localStorage.getItem(`cafeReviews-${cafeid}`);
            const existingReviews = existingReviewsStr ? JSON.parse(existingReviewsStr) : [];
            localStorage.setItem(`cafeReviews-${cafeid}`, JSON.stringify([newReview, ...existingReviews]));
            sessionStorage.setItem('reviewSuccess', 'true'); // 팝업을 한 번만 표시하기 위해 유지
            // 히스토리에 여러 리뷰 목록 페이지가 쌓이지 않도록 push 대신 replace 사용
            router.replace(`/cafes/${cafeid}/reviews`);
        } catch (error) {
            console.error('Failed to submit review:', error);
            alert('리뷰 등록에 실패했습니다.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex flex-col h-[100dvh] bg-[#FFFFFF] overflow-hidden max-w-md mx-auto w-full relative">
            {/* 헤더 */}
            <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
                <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
                    <button
                        onClick={handleBack}
                        className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
                    </button>
                    <h1 className="text-[16px] font-bold text-gray-900">리뷰 작성</h1>
                    <div className="w-10 h-10 flex items-center justify-center bg-transparent" />
                </div>
            </header>

            <main className="flex-1 overflow-y-auto px-5 py-6 no-scrollbar flex flex-col items-center">
                <div className="w-full flex-1 flex flex-col justify-between">
                    <div className="w-full">
                        {/* 카페 이름 */}
                        <h2 className="text-[18px] font-bold text-gray-900 mb-4 tracking-tight">아우어베이커리 역삼점</h2>

                {/* 이미지 슬라이더 */}
                {previewUrls.length > 0 && (
                    <div className="flex overflow-x-auto gap-2 pb-2 mb-4 snap-x snap-mandatory no-scrollbar -mx-5 px-5">
                        <AnimatePresence>
                            {previewUrls.map((url, index) => (
                                <motion.div
                                    key={url}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8, filter: 'blur(4px)' }}
                                    transition={{ duration: 0.2 }}
                                    className="relative flex-shrink-0 w-full aspect-[4/3] snap-center rounded-2xl overflow-hidden shadow-sm"
                                >
                                    <Image
                                        src={url}
                                        alt={`preview-${index}`}
                                        fill
                                        className="object-cover"
                                    />
                                    <button
                                        onClick={() => removeImage(index)}
                                        className="absolute bottom-3 right-3 w-[34px] h-[34px] rounded-full bg-black/30 backdrop-blur-md flex items-center justify-center transition-all active:scale-90"
                                    >
                                        <Image src="/images/review/deleteIcon.png" alt="delete" width={18} height={18} />
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                )}

                {/* 별점 */}
                <div className="flex items-center gap-2 mb-6 mt-4">
                    <span className="text-[16px] font-bold font-pretendard whitespace-nowrap mr-1 text-gray-800">별점 :</span>
                    <div
                        ref={starContainerRef}
                        className="flex items-center gap-1 cursor-pointer touch-none"
                        onPointerDown={handleStarPointerDown}
                        onPointerMove={handleStarPointerMove}
                    >
                        {[1, 2, 3, 4, 5].map((starValue) => {
                            if (rating >= starValue) {
                                return <Star key={starValue} className="w-[32px] h-[32px] fill-[#FFD700] text-[#FFD700] shrink-0" strokeWidth={1} />;
                            } else if (rating >= starValue - 0.5) {
                                return (
                                    <div key={starValue} className="relative w-[32px] h-[32px] shrink-0">
                                        <Star className="absolute top-0 left-0 w-[32px] h-[32px] text-[#E5E7EB]" fill="#E5E7EB" strokeWidth={1} />
                                        <div className="absolute top-0 left-0 w-[16px] h-[32px] overflow-hidden">
                                            <Star className="w-[32px] h-[32px] text-[#FFD700] fill-[#FFD700]" strokeWidth={1} />
                                        </div>
                                    </div>
                                );
                            } else {
                                return <Star key={starValue} className="w-[32px] h-[32px] text-[#E5E7EB]" fill="#E5E7EB" strokeWidth={1} />;
                            }
                        })}
                    </div>
                </div>

                {/* 내용 */}
                <div className="mb-2">
                    <Input
                        isMultiline
                        placeholder="직접 방문한 후기를 작성해주세요."
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        className="h-[140px] rounded-[16px] text-[15px] pt-4 px-4 bg-white border border-gray-200"
                    />
                </div>
                
                {(images.length === 0 || isOverLimit) && (
                    <div className="w-full text-center mt-2 mb-2">
                        <span className="text-[14px] text-[#c8325a] font-pretendard tracking-tight">리뷰 사진은 최대 3개까지 등록 가능합니다.</span>
                    </div>
                )}
                </div>

                {/* 하단 동작 */}
                <div className="w-full pt-4 pb-4 flex items-center justify-between z-10 gap-4 mt-auto">
                    <input
                        type="file"
                        multiple
                        accept="image/*"
                        ref={fileInputRef}
                        className="hidden"
                        onChange={handleImageUpload}
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="w-[50px] h-[50px] rounded-full border-[2px] border-black flex items-center justify-center shrink-0 active:scale-95 transition-transform bg-white"
                    >
                        <Camera className="w-[24px] h-[24px] text-black" strokeWidth={1.5} />
                    </button>

                    <Button
                        onClick={handleSubmit}
                        disabled={isSubmitting || images.length === 0 || rating === 0 || !content.trim()}
                        variant={(images.length === 0 || rating === 0 || !content.trim()) ? 'gray' : 'primary'}
                        className="!w-[110px] !h-[40px] rounded-full text-sm font-medium !px-0"
                    >
                        저장
                    </Button>
                </div>
            </div>
            </main>
        </div>
    );
}
