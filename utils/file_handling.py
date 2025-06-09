# utils/file_handling.py
# type: ignore

import os
import hashlib
import mimetypes
from typing import Optional, Dict, Any, Tuple
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
import logging
import magic  # python-magic for file type detection

logger = logging.getLogger(__name__)

class FileUploadService:
    """
    Comprehensive file upload service for the streaming platform
    Handles videos, images, audio, and documents with security and optimization
    """
    
    # Allowed file types
    ALLOWED_VIDEO_TYPES = [
        'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo',
        'video/webm', 'video/x-flv', 'video/3gpp', 'video/x-ms-wmv'
    ]
    
    ALLOWED_IMAGE_TYPES = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 
        'image/bmp', 'image/tiff', 'image/svg+xml'
    ]
    
    ALLOWED_AUDIO_TYPES = [
        'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/ogg',
        'audio/mp4', 'audio/aac', 'audio/x-aac', 'audio/flac',
        'audio/x-flac', 'audio/webm'
    ]
    
    ALLOWED_DOCUMENT_TYPES = [
        'application/pdf', 'text/plain', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    # File size limits (in bytes) - Set to None for unlimited
    MAX_VIDEO_SIZE = None  # Unlimited as requested
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB for images
    MAX_AUDIO_SIZE = None  # Unlimited for audio
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB for documents
    
    def __init__(self):
        self.use_cloudinary = getattr(settings, 'USE_CLOUDINARY', False)
        
        if self.use_cloudinary:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
                api_key=settings.CLOUDINARY_STORAGE.get('API_KEY'),
                api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET'),
            )
    
    def upload_file(self, file: UploadedFile, upload_type: str, 
                   folder: str = None, **kwargs) -> Dict[str, Any]:
        """
        Main upload method that handles all file types
        
        Args:
            file: The uploaded file
            upload_type: 'video', 'image', 'audio', or 'document'
            folder: Optional folder name for organization
            **kwargs: Additional options
        
        Returns:
            Dictionary with upload results
        """
        
        try:
            # Validate file
            validation_result = self._validate_file(file, upload_type)
            if not validation_result['valid']:
                return validation_result
            
            # Generate secure filename
            secure_filename = self._generate_secure_filename(file.name)
            
            # Calculate file hash for deduplication
            file_hash = self._calculate_file_hash(file)
            
            # Check for existing file with same hash
            existing_file = self._check_existing_file(file_hash)
            if existing_file:
                logger.info(f"File already exists with hash {file_hash}")
                return {
                    'success': True,
                    'message': 'File already exists',
                    'url': existing_file['url'],
                    'public_id': existing_file['public_id'],
                    'file_hash': file_hash,
                    'duplicate': True
                }
            
            # Upload based on storage type
            if self.use_cloudinary:
                result = self._upload_to_cloudinary(file, upload_type, folder, secure_filename, **kwargs)
            else:
                result = self._upload_to_local_storage(file, upload_type, folder, secure_filename, **kwargs)
            
            # Add metadata
            result.update({
                'file_hash': file_hash,
                'original_filename': file.name,
                'file_size': file.size,
                'content_type': file.content_type,
                'upload_type': upload_type
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading file {file.name}: {e}")
            return {
                'success': False,
                'error': f'Upload failed: {str(e)}'
            }
    
    def delete_file(self, public_id: str, resource_type: str = 'auto') -> bool:
        """Delete file from storage"""
        
        try:
            if self.use_cloudinary:
                result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
                return result.get('result') == 'ok'
            else:
                # Handle local file deletion
                file_path = os.path.join(settings.MEDIA_ROOT, public_id)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {public_id}: {e}")
            return False
    
    def generate_thumbnails(self, video_url: str, timestamps: list = None) -> list:
        """Generate thumbnails from video at specified timestamps"""
        
        if not timestamps:
            timestamps = [0, 30, 60, 120]  # Default timestamps in seconds
        
        thumbnails = []
        
        if self.use_cloudinary:
            try:
                for timestamp in timestamps:
                    thumbnail_url = cloudinary.utils.cloudinary_url(
                        video_url,
                        format="jpg",
                        start_offset=f"{timestamp}s",
                        transformation=[
                            {'width': 480, 'height': 270, 'crop': 'fill'},
                            {'quality': 'auto'}
                        ]
                    )[0]
                    
                    thumbnails.append({
                        'timestamp': timestamp,
                        'url': thumbnail_url
                    })
                    
            except Exception as e:
                logger.error(f"Error generating thumbnails: {e}")
        
        return thumbnails
    
    def optimize_image(self, image_url: str, width: int = None, height: int = None, 
                      quality: str = 'auto') -> str:
        """Generate optimized version of an image"""
        
        if self.use_cloudinary:
            try:
                transformations = []
                
                if width or height:
                    transformations.append({
                        'width': width,
                        'height': height,
                        'crop': 'fill' if width and height else 'scale'
                    })
                
                transformations.append({'quality': quality})
                
                optimized_url = cloudinary.utils.cloudinary_url(
                    image_url,
                    transformation=transformations
                )[0]
                
                return optimized_url
                
            except Exception as e:
                logger.error(f"Error optimizing image: {e}")
                return image_url
        
        return image_url
    
    def get_file_metadata(self, file_url: str) -> Dict[str, Any]:
        """Get metadata for an uploaded file"""
        
        if self.use_cloudinary:
            try:
                # Extract public_id from URL
                public_id = self._extract_public_id_from_url(file_url)
                
                resource = cloudinary.api.resource(public_id)
                
                return {
                    'file_size': resource.get('bytes'),
                    'format': resource.get('format'),
                    'width': resource.get('width'),
                    'height': resource.get('height'),
                    'duration': resource.get('duration'),
                    'created_at': resource.get('created_at'),
                    'resource_type': resource.get('resource_type')
                }
                
            except Exception as e:
                logger.error(f"Error getting file metadata: {e}")
                return {}
        
        return {}
    
    def _validate_file(self, file: UploadedFile, upload_type: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        
        # Check file size
        size_limits = {
            'video': self.MAX_VIDEO_SIZE,
            'image': self.MAX_IMAGE_SIZE,
            'audio': self.MAX_AUDIO_SIZE,
            'document': self.MAX_DOCUMENT_SIZE
        }
        
        max_size = size_limits.get(upload_type)
        if max_size and file.size > max_size:
            return {
                'valid': False,
                'error': f'File size exceeds maximum allowed size of {max_size / (1024*1024):.1f}MB'
            }
        
        # Check file type
        detected_type = self._detect_file_type(file)
        allowed_types = {
            'video': self.ALLOWED_VIDEO_TYPES,
            'image': self.ALLOWED_IMAGE_TYPES,
            'audio': self.ALLOWED_AUDIO_TYPES,
            'document': self.ALLOWED_DOCUMENT_TYPES
        }
        
        if detected_type not in allowed_types.get(upload_type, []):
            return {
                'valid': False,
                'error': f'File type {detected_type} not allowed for {upload_type} uploads'
            }
        
        # Additional security checks
        if not self._is_safe_filename(file.name):
            return {
                'valid': False,
                'error': 'Filename contains unsafe characters'
            }
        
        return {'valid': True}
    
    def _detect_file_type(self, file: UploadedFile) -> str:
        """Detect actual file type using python-magic"""
        
        try:
            # Read first 2048 bytes for type detection
            file.seek(0)
            header = file.read(2048)
            file.seek(0)
            
            # Use python-magic for accurate detection
            mime_type = magic.from_buffer(header, mime=True)
            return mime_type
            
        except Exception as e:
            logger.warning(f"Could not detect file type with magic: {e}")
            # Fallback to content type from upload
            return file.content_type or 'application/octet-stream'
    
    def _generate_secure_filename(self, original_filename: str) -> str:
        """Generate secure filename"""
        
        # Extract extension
        name, ext = os.path.splitext(original_filename)
        
        # Generate hash-based filename
        import uuid
        secure_name = str(uuid.uuid4())
        
        return f"{secure_name}{ext.lower()}"
    
    def _calculate_file_hash(self, file: UploadedFile) -> str:
        """Calculate SHA-256 hash of file content"""
        
        hasher = hashlib.sha256()
        
        file.seek(0)
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
        file.seek(0)
        
        return hasher.hexdigest()
    
    def _check_existing_file(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Check if file with same hash already exists"""
        
        # This would check your database for existing files with the same hash
        # For now, return None (no duplicate detection)
        # In a real implementation, you'd query your file storage records
        
        return None
    
    def _upload_to_cloudinary(self, file: UploadedFile, upload_type: str, 
                             folder: str, filename: str, **kwargs) -> Dict[str, Any]:
        """Upload file to Cloudinary"""
        
        resource_type_map = {
            'video': 'video',
            'image': 'image',
            'audio': 'video',  # Cloudinary treats audio as video
            'document': 'raw'
        }
        
        resource_type = resource_type_map.get(upload_type, 'auto')
        
        upload_options = {
            'resource_type': resource_type,
            'public_id': f"{folder}/{filename}" if folder else filename,
            'overwrite': True,
            'invalidate': True,
        }
        
        # Add video-specific options
        if upload_type == 'video':
            upload_options.update({
                'eager': [
                    {'format': 'mp4', 'quality': 'auto'},
                    {'format': 'webm', 'quality': 'auto'}
                ],
                'eager_async': True,
            })
        
        # Add image-specific options
        elif upload_type == 'image':
            upload_options.update({
                'quality': 'auto',
                'fetch_format': 'auto',
            })
        
        result = cloudinary.uploader.upload(file, **upload_options)
        
        return {
            'success': True,
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'version': result.get('version'),
            'format': result.get('format'),
            'width': result.get('width'),
            'height': result.get('height'),
            'duration': result.get('duration'),
        }
    
    def _upload_to_local_storage(self, file: UploadedFile, upload_type: str,
                                folder: str, filename: str, **kwargs) -> Dict[str, Any]:
        """Upload file to local storage (development only)"""
        
        upload_path = os.path.join(settings.MEDIA_ROOT, upload_type, folder or '', filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        
        with open(upload_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        relative_path = os.path.join(upload_type, folder or '', filename)
        file_url = os.path.join(settings.MEDIA_URL, relative_path).replace('\\', '/')
        
        return {
            'success': True,
            'url': file_url,
            'public_id': relative_path,
            'local_path': upload_path
        }
    
    def _is_safe_filename(self, filename: str) -> bool:
        """Check if filename is safe"""
        
        unsafe_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return not any(char in filename for char in unsafe_chars)
    
    def _extract_public_id_from_url(self, url: str) -> str:
        """Extract public_id from Cloudinary URL"""
        
        try:
            # Basic extraction - in real implementation, use Cloudinary utils
            parts = url.split('/')
            filename = parts[-1]
            public_id = filename.split('.')[0]
            return public_id
        except:
            return url

# Global file upload service instance
file_upload_service = FileUploadService()

# Convenience functions
def upload_video(video_file: UploadedFile, folder: str = 'videos', **kwargs) -> Dict[str, Any]:
    """Upload video file"""
    return file_upload_service.upload_file(video_file, 'video', folder, **kwargs)

def upload_image(image_file: UploadedFile, folder: str = 'images', **kwargs) -> Dict[str, Any]:
    """Upload image file"""
    return file_upload_service.upload_file(image_file, 'image', folder, **kwargs)

def upload_audio(audio_file: UploadedFile, folder: str = 'audio', **kwargs) -> Dict[str, Any]:
    """Upload audio file"""
    return file_upload_service.upload_file(audio_file, 'audio', folder, **kwargs)

def upload_document(document_file: UploadedFile, folder: str = 'documents', **kwargs) -> Dict[str, Any]:
    """Upload document file"""
    return file_upload_service.upload_file(document_file, 'document', folder, **kwargs)

def delete_uploaded_file(public_id: str, resource_type: str = 'auto') -> bool:
    """Delete uploaded file"""
    return file_upload_service.delete_file(public_id, resource_type)

def generate_video_thumbnails(video_url: str, timestamps: list = None) -> list:
    """Generate video thumbnails"""
    return file_upload_service.generate_thumbnails(video_url, timestamps)

def optimize_uploaded_image(image_url: str, width: int = None, height: int = None) -> str:
    """Optimize uploaded image"""
    return file_upload_service.optimize_image(image_url, width, height)