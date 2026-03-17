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

    // Clean up preview URLs
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
                // If the total images exceed 3, show the notice text and don't add
                // Using an empty return prevents the file upload
                setIsOverLimit(true);
            } else {
                setIsOverLimit(false);
                setImages(prev => [...prev, ...fileArray]);
                const urls = fileArray.map(file => URL.createObjectURL(file));
                setPreviewUrls(prev => [...prev, ...urls]);
            }
        }
        // Reset file input value so same files can be selected again if needed
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
        // Calculate the relative mouse position within the star container
        // Total width is roughly 5 stars + gaps (4 gaps). Let's calculate per star index.
        const gap = 4; // gap-1 is 4px
        const starWidth = 32; // w-[32px] is 32px

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
                // clicked in gap, consider it as the previous star full
                newRating = i + 1;
                break;
            } else if (x > starEnd) {
                newRating = i + 1; // Passed this star
            }
        }

        if (newRating > 0) {
            setRating(newRating);
        }
    };

    // Allow dragging pointer over stars
    const handleStarPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
        if (e.buttons !== 1) return; // Only trigger while mouse button is held down
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

            // Assuming API call is made here with formData
            // Example: await fetch(`/api/cafes/${cafeid}/reviews`, { method: 'POST', body: formData })
            console.log('Sending Review Data:', {
                rating,
                content,
                imageCount: images.length
            });

            // Read image as base64 to store in localStorage
            let base64Image = '/images/cafe/cafe1.png'; // default
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

            // Save to localStorage
            const existingReviewsStr = localStorage.getItem(`cafeReviews-${cafeid}`);
            const existingReviews = existingReviewsStr ? JSON.parse(existingReviewsStr) : [];
            localStorage.setItem(`cafeReviews-${cafeid}`, JSON.stringify([newReview, ...existingReviews]));
            sessionStorage.setItem('reviewSuccess', 'true'); // Keep this for showing popup once

            router.push(`/cafes/${cafeid}/reviews`);
        } catch (error) {
            console.error('Failed to submit review:', error);
            alert('리뷰 등록에 실패했습니다.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="flex flex-col h-[100dvh] bg-[#FFFFFF] overflow-hidden max-w-md mx-auto w-full relative">
            {/* Header */}
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
                        {/* Cafe Name */}
                        <h2 className="text-[18px] font-bold text-gray-900 mb-4 tracking-tight">아우어베이커리 역삼점</h2>

                {/* Image Slider */}
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

                {/* Rating */}
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

                {/* Content */}
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

                {/* Bottom Actions */}
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
