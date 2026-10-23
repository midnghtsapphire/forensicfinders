"""EXIF metadata reader salvaged as-is from revvel-forensic-studio cli/src/forensic_analysis.py (EXIFAnalyzer).
Only change: _extract_camera_info returns None when make and model are both empty, so the
"Missing camera information" indicator can fire (it was dead code), and _serialize_exif skips the
non-dict "thumbnail" entry (the original crashed on every image that had EXIF).
Output is metadata only; "manipulation_indicators" are heuristics, not proof of editing."""
from typing import Dict, List, Optional
import logging
import piexif
from PIL import Image

logger = logging.getLogger(__name__)


class EXIFAnalyzer:
    """Analyze and recover EXIF metadata from images."""
    
    def analyze(self, image_path: str) -> Dict:
        """
        Extract and analyze EXIF data.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Dictionary with EXIF data and analysis
        """
        try:
            img = Image.open(image_path)
            exif_dict = piexif.load(img.info.get("exif", b""))
            
            # Extract key metadata
            metadata = {
                "camera": self._extract_camera_info(exif_dict),
                "location": self._extract_location(exif_dict),
                "datetime": self._extract_datetime(exif_dict),
                "settings": self._extract_camera_settings(exif_dict),
                "software": self._extract_software_info(exif_dict),
                "raw_exif": self._serialize_exif(exif_dict)
            }
            
            # Analyze for manipulation
            metadata["manipulation_indicators"] = self._detect_manipulation(exif_dict)
            
            return metadata
        
        except Exception as e:
            logger.error(f"EXIF analysis error: {e}")
            return {
                "error": str(e),
                "camera": None,
                "location": None,
                "datetime": None
            }
    
    def _extract_camera_info(self, exif_dict: Dict) -> Optional[Dict]:
        """Extract camera information."""
        try:
            ifd0 = exif_dict.get("0th", {})
            exif = exif_dict.get("Exif", {})
            
            info = {
                "make": ifd0.get(piexif.ImageIFD.Make, b"").decode("utf-8", errors="ignore"),
                "model": ifd0.get(piexif.ImageIFD.Model, b"").decode("utf-8", errors="ignore"),
                "lens": exif.get(piexif.ExifIFD.LensModel, b"").decode("utf-8", errors="ignore")
            }
            return info if (info["make"] or info["model"]) else None
        except:
            return None
    
    def _extract_location(self, exif_dict: Dict) -> Optional[Dict]:
        """Extract GPS location."""
        try:
            gps = exif_dict.get("GPS", {})
            if not gps:
                return None
            
            lat = self._convert_to_degrees(gps.get(piexif.GPSIFD.GPSLatitude, []))
            lon = self._convert_to_degrees(gps.get(piexif.GPSIFD.GPSLongitude, []))
            
            lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef, b"N").decode()
            lon_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef, b"E").decode()
            
            if lat_ref == "S":
                lat = -lat
            if lon_ref == "W":
                lon = -lon
            
            return {
                "latitude": lat,
                "longitude": lon,
                "altitude": gps.get(piexif.GPSIFD.GPSAltitude, None)
            }
        except:
            return None
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to degrees."""
        if not value or len(value) != 3:
            return 0
        d = value[0][0] / value[0][1]
        m = value[1][0] / value[1][1]
        s = value[2][0] / value[2][1]
        return d + (m / 60.0) + (s / 3600.0)
    
    def _extract_datetime(self, exif_dict: Dict) -> Optional[str]:
        """Extract datetime information."""
        try:
            exif = exif_dict.get("Exif", {})
            dt = exif.get(piexif.ExifIFD.DateTimeOriginal, b"").decode("utf-8", errors="ignore")
            return dt if dt else None
        except:
            return None
    
    def _extract_camera_settings(self, exif_dict: Dict) -> Dict:
        """Extract camera settings."""
        try:
            exif = exif_dict.get("Exif", {})
            return {
                "iso": exif.get(piexif.ExifIFD.ISOSpeedRatings, None),
                "exposure_time": exif.get(piexif.ExifIFD.ExposureTime, None),
                "f_number": exif.get(piexif.ExifIFD.FNumber, None),
                "focal_length": exif.get(piexif.ExifIFD.FocalLength, None),
                "flash": exif.get(piexif.ExifIFD.Flash, None)
            }
        except:
            return {}
    
    def _extract_software_info(self, exif_dict: Dict) -> Optional[str]:
        """Extract software/editing information."""
        try:
            ifd0 = exif_dict.get("0th", {})
            software = ifd0.get(piexif.ImageIFD.Software, b"").decode("utf-8", errors="ignore")
            return software if software else None
        except:
            return None
    
    def _serialize_exif(self, exif_dict: Dict) -> Dict:
        """Serialize EXIF dict to JSON-compatible format."""
        result = {}
        for ifd_name, ifd_data in exif_dict.items():
            if not isinstance(ifd_data, dict):  # piexif puts the thumbnail (bytes/None) here
                continue
            result[ifd_name] = {}
            for tag, value in ifd_data.items():
                try:
                    if isinstance(value, bytes):
                        result[ifd_name][str(tag)] = value.decode("utf-8", errors="ignore")
                    else:
                        result[ifd_name][str(tag)] = str(value)
                except:
                    pass
        return result
    
    def _detect_manipulation(self, exif_dict: Dict) -> List[str]:
        """Detect indicators of image manipulation."""
        indicators = []
        
        # Check for editing software
        software = self._extract_software_info(exif_dict)
        if software and any(editor in software.lower() for editor in ["photoshop", "gimp", "lightroom"]):
            indicators.append(f"Edited with: {software}")
        
        # Check for missing expected EXIF data
        if not self._extract_camera_info(exif_dict):
            indicators.append("Missing camera information")
        
        if not self._extract_datetime(exif_dict):
            indicators.append("Missing datetime information")
        
        return indicators

