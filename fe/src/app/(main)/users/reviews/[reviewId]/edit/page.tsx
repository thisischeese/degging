'use client';

import React, { useState, useRef, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { Camera, ArrowLeft, Star, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/common/components/Input';
import Button from '@/common/components/Button';
import Image from 'next/image';

interface LocalReview {
  id: string;
  rating: number;
  content: string;
  imageUrl: string;
  timestamp: number;
}

const DEFAULT_CAFE_NAME = '카페';
const DEFAULT_IMAGE = '/images/cafe/cafe1.png';
const DEFAULT_CONTENT =
  '분위기가 조용해서 편하게 머물기 좋았고, 디저트와 커피도 전체적으로 만족스러웠어요.';

export default function MyReviewEditPage({
  params,
}: {
  params: Promise<{ reviewId: string }> | { reviewId: string };
}) {
  const router = useRouter();
  const resolvedParams = params instanceof Promise ? use(params) : params;
  const reviewId = resolvedParams.reviewId;

  const [rating, setRating] = useState<number>(0);
  const [content, setContent] = useState<string>('');
  const [images, setImages] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isOverLimit, setIsOverLimit] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const starContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isLocalFound = false;

    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith('cafeReviews-')) continue;

      try {
        const localReviews: LocalReview[] = JSON.parse(localStorage.getItem(key) || '[]');
        const foundReview = localReviews.find((review) => review.id === reviewId);

        if (foundReview) {
          setRating(foundReview.rating);
          setContent(foundReview.content);
          setPreviewUrls([foundReview.imageUrl]);
          isLocalFound = true;
          break;
        }
      } catch (error) {
        console.error(error);
      }
    }

    if (!isLocalFound) {
      setRating(3.5);
      setContent(DEFAULT_CONTENT);
      setPreviewUrls([DEFAULT_IMAGE]);
    }
  }, [reviewId]);

  useEffect(() => {
    return () => {
      previewUrls.forEach((url) => {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      });
    };
  }, [previewUrls]);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const fileArray = Array.from(event.target.files);
      const totalImages = previewUrls.length + fileArray.length;

      if (totalImages > 3) {
        setIsOverLimit(true);
      } else {
        setIsOverLimit(false);
        setImages((prev) => [...prev, ...fileArray]);
        const urls = fileArray.map((file) => URL.createObjectURL(file));
        setPreviewUrls((prev) => [...prev, ...urls]);
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeImage = (indexToRemove: number) => {
    setPreviewUrls((prev) => {
      const nextUrls = [...prev];
      const targetUrl = nextUrls[indexToRemove];

      if (targetUrl?.startsWith('blob:')) {
        URL.revokeObjectURL(targetUrl);
      }

      nextUrls.splice(indexToRemove, 1);
      return nextUrls;
    });
  };

  const handleStarPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!starContainerRef.current) return;

    const rect = starContainerRef.current.getBoundingClientRect();
    const gap = 4;
    const starWidth = 32;
    const x = event.clientX - rect.left;
    let nextRating = 0;

    for (let i = 0; i < 5; i++) {
      const starStart = i * (starWidth + gap);
      const starEnd = starStart + starWidth;

      if (x >= starStart && x <= starEnd) {
        const relativeX = x - starStart;
        nextRating = relativeX < starWidth / 2 ? i + 0.5 : i + 1;
        break;
      }

      if (i < 4 && x > starEnd && x < starEnd + gap) {
        nextRating = i + 1;
        break;
      }

      if (x > starEnd) {
        nextRating = i + 1;
      }
    }

    if (nextRating > 0) {
      setRating(nextRating);
    }
  };

  const handleStarPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.buttons !== 1) return;
    handleStarPointerDown(event);
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);

      let finalImage = previewUrls[0] || DEFAULT_IMAGE;
      if (images.length > 0) {
        const file = images[images.length - 1];
        const fileReader = new FileReader();
        const base64Promise = new Promise<string>((resolve) => {
          fileReader.onload = () => resolve(fileReader.result as string);
          fileReader.onerror = () => resolve(DEFAULT_IMAGE);
        });
        fileReader.readAsDataURL(file);
        finalImage = await base64Promise;
      }

      let updated = false;
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (!key || !key.startsWith('cafeReviews-')) continue;

        try {
          const localReviews: LocalReview[] = JSON.parse(localStorage.getItem(key) || '[]');
          const targetIndex = localReviews.findIndex((review) => review.id === reviewId);

          if (targetIndex !== -1) {
            localReviews[targetIndex] = {
              ...localReviews[targetIndex],
              rating,
              content,
              imageUrl: finalImage,
            };
            localStorage.setItem(key, JSON.stringify(localReviews));
            updated = true;
            break;
          }
        } catch {}
      }

      if (updated) {
        alert('리뷰가 수정되었습니다.');
      } else {
        alert('목업 리뷰를 찾지 못했습니다.');
      }

      router.replace(`/users/reviews/${reviewId}`);
    } catch (error) {
      console.error('Failed to update review:', error);
      alert('리뷰 수정에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex flex-col h-[100dvh] bg-[#FFFFFF] overflow-hidden max-w-md mx-auto w-full relative">
      <header className="sticky top-0 z-10 bg-[#F9F9F4] border-b border-gray-200">
        <div className="flex items-center justify-between h-14 px-4 pt-safe-top">
          <button
            onClick={() => router.back()}
            className="w-10 h-10 flex items-center justify-center rounded-full border border-gray-900 bg-transparent hover:bg-gray-100 transition-colors z-10"
          >
            <ArrowLeft className="w-5 h-5 text-gray-900" strokeWidth={1.2} />
          </button>
          <h1 className="text-[16px] font-bold text-gray-900 absolute left-1/2 -translate-x-1/2">
            리뷰 수정
          </h1>
          <div className="w-10 h-10 flex items-center justify-center bg-transparent z-10" />
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-5 py-6 pb-28 no-scrollbar flex flex-col items-center">
        <div className="w-full flex-1 flex flex-col justify-start">
          <div className="w-full">
            <h2 className="text-[18px] font-bold text-gray-900 mb-4 tracking-tight">{DEFAULT_CAFE_NAME}</h2>

            {previewUrls.length > 0 && (
              <div className="flex overflow-x-auto gap-2 pb-2 mb-4 snap-x snap-mandatory no-scrollbar -mx-5 px-5">
                <AnimatePresence>
                  {previewUrls.map((url, index) => (
                    <motion.div
                      key={`${url}-${index}`}
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
                        unoptimized
                      />
                      <button
                        onClick={() => removeImage(index)}
                        className="absolute bottom-3 right-3 w-[34px] h-[34px] rounded-full bg-black/30 backdrop-blur-md flex items-center justify-center transition-all active:scale-90 overflow-hidden"
                      >
                        <Image
                          src="/images/review/deleteIcon.png"
                          alt="delete"
                          height={18}
                          width={18}
                          className="object-contain"
                          onError={(event) => {
                            event.currentTarget.style.display = 'none';
                          }}
                        />
                        <Trash2 size={16} className="text-white absolute" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}

            <div className="flex items-center gap-2 mb-6 mt-4">
              <span className="text-[16px] font-bold font-pretendard whitespace-nowrap mr-1 text-gray-800">
                별점 :
              </span>
              <div
                ref={starContainerRef}
                className="flex items-center gap-1 cursor-pointer touch-none"
                onPointerDown={handleStarPointerDown}
                onPointerMove={handleStarPointerMove}
              >
                {[1, 2, 3, 4, 5].map((starValue) => {
                  if (rating >= starValue) {
                    return (
                      <Star
                        key={starValue}
                        className="w-[32px] h-[32px] fill-[#FFD700] text-[#FFD700] shrink-0"
                        strokeWidth={1}
                      />
                    );
                  }

                  if (rating >= starValue - 0.5) {
                    return (
                      <div key={starValue} className="relative w-[32px] h-[32px] shrink-0">
                        <Star
                          className="absolute top-0 left-0 w-[32px] h-[32px] text-[#E5E7EB]"
                          fill="#E5E7EB"
                          strokeWidth={1}
                        />
                        <div className="absolute top-0 left-0 w-[16px] h-[32px] overflow-hidden">
                          <Star className="w-[32px] h-[32px] text-[#FFD700] fill-[#FFD700]" strokeWidth={1} />
                        </div>
                      </div>
                    );
                  }

                  return (
                    <Star
                      key={starValue}
                      className="w-[32px] h-[32px] text-[#E5E7EB]"
                      fill="#E5E7EB"
                      strokeWidth={1}
                    />
                  );
                })}
              </div>
            </div>

            <div className="mb-2">
              <Input
                isMultiline
                placeholder="직접 방문한 후기를 작성해 주세요."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="h-[140px] rounded-[16px] text-[15px] pt-4 px-4 bg-white border border-gray-200"
              />
            </div>

            {(previewUrls.length === 0 || isOverLimit) && (
              <div className="w-full text-center mt-2 mb-2">
                <span className="text-[14px] text-[#c8325a] font-pretendard tracking-tight">
                  리뷰 사진은 최대 3개까지 등록 가능합니다.
                </span>
              </div>
            )}
          </div>

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
              disabled={isSubmitting || previewUrls.length === 0 || rating === 0 || !content.trim()}
              variant={previewUrls.length === 0 || rating === 0 || !content.trim() ? 'gray' : 'primary'}
              className="!w-[110px] !h-[40px] rounded-full text-sm font-medium !px-0"
            >
              수정
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
