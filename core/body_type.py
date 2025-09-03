# import cv2
# import numpy as np
# import time
# import torch

# class BodyTypeDetector:
#     """
#     Ultra-fast body type detection with batch processing support
#     """
    
#     def __init__(self, pose_model):
#         self.pose_model = pose_model
        
#         # Optimize pose model for speed
#         if torch.cuda.is_available():
#             self.pose_model.half()  # Use FP16 for 2x speed
        
#         # Simple detection parameters
#         self.ankle_threshold = 0.
        
#         # Batch processing settings
#         self.max_batch_size = 16
#         self.batch_imgsz = 320  # Smaller size for faster processing
        
#     def detect_body_type(self, person_image, person_id=None, person_bbox=None):
#         """
#         Single person body type detection (fallback method)
#         Returns: 'full' or 'partial'
#         """
#         return self.detect_body_type_batch([person_image], [{'person_id': person_id, 'bbox': person_bbox}])[0]
    
#     def detect_body_type_batch(self, person_images, person_metadata=None):
#         """
#         Batch body type detection for multiple person crops
        
#         Args:
#             person_images: List of person crop images (numpy arrays)
#             person_metadata: List of metadata dicts with 'person_id' and 'bbox' keys
            
#         Returns:
#             List of body types ['full' or 'partial'] corresponding to input images
#         """
#         try:
#             if not person_images:
#                 return []
            
#             batch_size = len(person_images)
#             results = ['partial'] * batch_size  # Default to partial
            
#             # Prepare batch for pose model
#             processed_images = []
#             valid_indices = []
            
#             for i, img in enumerate(person_images):
#                 if img is not None and img.size > 0:
#                     # Resize to consistent size for batching
#                     if img.shape[0] > self.batch_imgsz or img.shape[1] > self.batch_imgsz:
#                         # Maintain aspect ratio
#                         h, w = img.shape[:2]
#                         scale = min(self.batch_imgsz / w, self.batch_imgsz / h)
#                         new_w = int(w * scale)
#                         new_h = int(h * scale)
#                         img = cv2.resize(img, (new_w, new_h))
                    
#                     processed_images.append(img)
#                     valid_indices.append(i)
            
#             if not processed_images:
#                 return results
            
#             # Process in sub-batches to avoid memory issues
#             for batch_start in range(0, len(processed_images), self.max_batch_size):
#                 batch_end = min(batch_start + self.max_batch_size, len(processed_images))
#                 batch_images = processed_images[batch_start:batch_end]
#                 batch_indices = valid_indices[batch_start:batch_end]
                
#                 # Run pose detection on batch
#                 try:
#                     pose_results = self.pose_model(
#                         batch_images, 
#                         verbose=False, 
#                         imgsz=self.batch_imgsz, 
#                         conf=0.1
#                     )
                    
#                     # Process each result in the batch
#                     for j, pose_result in enumerate(pose_results):
#                         original_idx = batch_indices[j]
                        
#                         if pose_result.keypoints is not None and len(pose_result.keypoints.data) > 0:
#                             # Get first person's keypoints
#                             keypoints = pose_result.keypoints.data[0].cpu().numpy()
                            
#                             # COCO format ankle indices
#                             LEFT_ANKLE = 15
#                             RIGHT_ANKLE = 16
                            
#                             # Check ankle visibility
#                             left_ankle_conf = keypoints[LEFT_ANKLE][2] if len(keypoints) > LEFT_ANKLE else 0
#                             right_ankle_conf = keypoints[RIGHT_ANKLE][2] if len(keypoints) > RIGHT_ANKLE else 0
                            
#                             # If either ankle is visible with good confidence = full body
#                             if left_ankle_conf > self.ankle_threshold or right_ankle_conf > self.ankle_threshold:
#                                 results[original_idx] = "full"
#                             else:
#                                 results[original_idx] = "partial"
#                         else:
#                             # No pose detected, use fallback
#                             metadata = person_metadata[original_idx] if person_metadata else None
#                             bbox = metadata.get('bbox') if metadata else None
#                             img = person_images[original_idx]
#                             results[original_idx] = self._fallback_detection(bbox, img)
                            
#                 except Exception as e:
#                     print(f"[ERROR] Batch pose detection failed: {e}")
#                     # Use fallback for all images in this batch
#                     for j in range(len(batch_images)):
#                         original_idx = batch_indices[j]
#                         metadata = person_metadata[original_idx] if person_metadata else None
#                         bbox = metadata.get('bbox') if metadata else None
#                         img = person_images[original_idx]
#                         results[original_idx] = self._fallback_detection(bbox, img)
            
#             return results
            
#         except Exception as e:
#             print(f"[ERROR] detect_body_type_batch: {e}")
#             # Return fallback results for all
#             results = []
#             for i, img in enumerate(person_images):
#                 metadata = person_metadata[i] if person_metadata else None
#                 bbox = metadata.get('bbox') if metadata else None
#                 results.append(self._fallback_detection(bbox, img))
#             return results
    
#     def _fallback_detection(self, person_bbox, person_image):
#         """
#         Simple fallback based on aspect ratio
#         """
#         try:
#             if person_bbox is not None:
#                 x1, y1, x2, y2 = person_bbox
#                 height = y2 - y1
#                 width = x2 - x1
#                 aspect_ratio = height / (width + 1e-5)
                
#                 # Simple rule: tall and narrow = likely full body
#                 if height > 200 and aspect_ratio > 2.2:
#                     return "full"
#                 else:
#                     return "partial"
#             else:
#                 # Use image dimensions
#                 if person_image is not None and person_image.size > 0:
#                     height, width = person_image.shape[:2]
#                     aspect_ratio = height / (width + 1e-5)
                    
#                     if height > 150 and aspect_ratio > 2.0:
#                         return "full"
#                     else:
#                         return "partial"
                        
#         except Exception:
#             pass
            
#         return "partial"  # Default fallback
    
#     def get_batch_statistics(self):
#         """
#         Get statistics about batch processing performance
#         """
#         return {
#             'max_batch_size': self.max_batch_size,
#             'batch_imgsz': self.batch_imgsz,
#             'ankle_threshold': self.ankle_threshold
#         }