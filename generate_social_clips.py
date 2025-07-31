#!/usr/bin/env python3
"""
Social Media Video Clip Generator
Generates optimized video clips for different social media platforms
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime
import shutil

class SocialMediaClipGenerator:
    def __init__(self, source_video, enhanced_audio, output_dir="output_clips"):
        self.source_video = Path(source_video)
        self.enhanced_audio = Path(enhanced_audio)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Platform specifications
        self.platform_specs = {
            "tiktok": {
                "aspect_ratio": "9:16",
                "max_duration": 60,
                "resolution": "1080x1920",
                "video_codec": "libx264",
                "audio_codec": "aac",
                "crf": 23,
                "preset": "fast"
            },
            "youtube_shorts": {
                "aspect_ratio": "9:16", 
                "max_duration": 60,
                "resolution": "1080x1920",
                "video_codec": "libx264",
                "audio_codec": "aac",
                "crf": 23,
                "preset": "fast"
            },
            "twitter": {
                "aspect_ratio": "16:9",
                "max_duration": 140,  # 2:20
                "resolution": "1280x720",
                "video_codec": "libx264",
                "audio_codec": "aac",
                "crf": 23,
                "preset": "fast"
            },
            "linkedin": {
                "aspect_ratio": "16:9",
                "max_duration": 600,  # 10 minutes
                "resolution": "1920x1080",
                "video_codec": "libx264",
                "audio_codec": "aac",
                "crf": 23,
                "preset": "fast"
            }
        }
        
        # Viral moments from content analysis
        self.viral_moments = [
            {
                "id": "100x_powerful",
                "start": "00:00:12.145",
                "end": "00:00:17.354",
                "text": "OpenAI will absolutely release GPT-5.0 this summer, and it's going to be 100 times more powerful than GPT-4!",
                "platforms": ["tiktok", "youtube_shorts", "twitter"],
                "title": "GPT-5 is 100X MORE POWERFUL?!"
            },
            {
                "id": "phd_level",
                "start": "00:00:17.880", 
                "end": "00:00:23.561",
                "text": "The leaked benchmarks show GPT-5 solving PhD-level problems in seconds - this changes everything for education and research!",
                "platforms": ["tiktok", "youtube_shorts", "twitter", "linkedin"],
                "title": "PhD Problems SOLVED in SECONDS"
            },
            {
                "id": "sam_altman",
                "start": "00:00:06.367",
                "end": "00:00:11.439", 
                "text": "Sam Altman hinted at a 'summer surprise' - industry insiders confirm it's GPT-5.0 with multimodal capabilities",
                "platforms": ["twitter", "linkedin"],
                "title": "Sam Altman's SECRET Summer Surprise"
            },
            {
                "id": "combined_short",
                "start": "00:00:06.367",
                "end": "00:00:23.561",
                "text": "Combined viral moments",
                "platforms": ["youtube_shorts"],
                "title": "GPT-5.0 CONFIRMED: Everything You Need to Know"
            }
        ]
        
    def generate_subtitles(self, moment, output_path):
        """Generate SRT subtitle file for a clip"""
        # Calculate duration properly
        start_seconds = sum(float(x) * 60 ** i for i, x in enumerate(reversed(moment['start'].split(':'))))
        end_seconds = sum(float(x) * 60 ** i for i, x in enumerate(reversed(moment['end'].split(':'))))
        duration = end_seconds - start_seconds
        
        # Format duration for SRT
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        milliseconds = int((duration % 1) * 1000)
        
        srt_content = f"""1
00:00:00,000 --> {hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}
{moment['text']}
"""
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        return output_path
    
    def crop_to_vertical(self, input_file, output_file):
        """Crop video to 9:16 vertical aspect ratio"""
        cmd = [
            "ffmpeg", "-i", str(input_file),
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264", "-crf", "23", "-preset", "fast",
            "-c:a", "copy",
            "-y", str(output_file)
        ]
        subprocess.run(cmd, check=True)
        return output_file
    
    def generate_clip(self, moment, platform):
        """Generate a clip for a specific platform"""
        platform_spec = self.platform_specs[platform]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create platform directory
        platform_dir = self.output_dir / platform
        platform_dir.mkdir(exist_ok=True)
        
        # Output filename
        output_filename = f"{moment['id']}_{platform}_{timestamp}.mp4"
        output_path = platform_dir / output_filename
        
        # Generate subtitles
        srt_path = platform_dir / f"{moment['id']}_subtitles.srt"
        self.generate_subtitles(moment, srt_path)
        
        # Calculate duration properly
        start_seconds = sum(float(x) * 60 ** i for i, x in enumerate(reversed(moment['start'].split(':'))))
        end_seconds = sum(float(x) * 60 ** i for i, x in enumerate(reversed(moment['end'].split(':'))))
        duration = end_seconds - start_seconds
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-ss", moment['start'],
            "-i", str(self.source_video),
            "-i", str(self.enhanced_audio),
            "-t", str(duration),
            "-map", "0:v:0",
            "-map", "1:a:0"
        ]
        
        # Add video filters
        filters = []
        
        # Aspect ratio adjustment
        if platform_spec['aspect_ratio'] == "9:16":
            # Vertical crop centering on the middle
            filters.append("crop=ih*9/16:ih")
        elif platform_spec['aspect_ratio'] == "1:1":
            # Square crop
            filters.append("crop=ih:ih")
        
        # Scale to target resolution
        if platform in ["twitter"]:
            filters.append(f"scale={platform_spec['resolution']}")
        elif platform in ["tiktok", "youtube_shorts"]:
            filters.append("scale=1080:1920")
            
        # Add subtitles with styling
        filters.append(f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2,Alignment=2,MarginV=50'")
        
        if filters:
            cmd.extend(["-vf", ",".join(filters)])
        
        # Video encoding
        cmd.extend([
            "-c:v", platform_spec['video_codec'],
            "-crf", str(platform_spec['crf']),
            "-preset", platform_spec['preset']
        ])
        
        # Audio encoding
        cmd.extend([
            "-c:a", platform_spec['audio_codec'],
            "-b:a", "128k",
            "-ar", "48000"
        ])
        
        # Output
        cmd.extend(["-y", str(output_path)])
        
        print(f"Generating {platform} clip: {output_filename}")
        subprocess.run(cmd, check=True)
        
        # Generate thumbnail
        thumbnail_path = platform_dir / f"{moment['id']}_thumbnail.jpg"
        self.generate_thumbnail(output_path, thumbnail_path, timestamp=duration / 2)
        
        return {
            "platform": platform,
            "clip_id": moment['id'],
            "filename": output_filename,
            "path": str(output_path),
            "thumbnail": str(thumbnail_path),
            "duration": duration,
            "title": moment['title'],
            "subtitles": str(srt_path)
        }
    
    def generate_thumbnail(self, video_path, output_path, timestamp=2.0):
        """Extract thumbnail from video at specified timestamp"""
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-ss", str(timestamp),
            "-vframes", "1",
            "-q:v", "2",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True)
    
    def generate_all_clips(self):
        """Generate all clips for all platforms"""
        results = {
            "generation_timestamp": datetime.now().isoformat(),
            "source_video": str(self.source_video),
            "enhanced_audio": str(self.enhanced_audio),
            "clips": []
        }
        
        for moment in self.viral_moments:
            for platform in moment['platforms']:
                try:
                    clip_info = self.generate_clip(moment, platform)
                    results['clips'].append(clip_info)
                    
                    # Get file size
                    file_size = os.path.getsize(clip_info['path'])
                    clip_info['file_size_mb'] = round(file_size / (1024 * 1024), 2)
                    
                except Exception as e:
                    print(f"Error generating {platform} clip for {moment['id']}: {e}")
                    results['clips'].append({
                        "platform": platform,
                        "clip_id": moment['id'],
                        "error": str(e)
                    })
        
        # Save results metadata
        metadata_path = self.output_dir / "generation_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nGeneration complete! Metadata saved to: {metadata_path}")
        return results
    
    def generate_platform_package(self, platform):
        """Create a zip package for a specific platform with all clips and metadata"""
        platform_dir = self.output_dir / platform
        if not platform_dir.exists():
            print(f"No clips found for {platform}")
            return
        
        # Create package
        package_name = f"{platform}_clips_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(
            str(self.output_dir / package_name),
            'zip',
            str(platform_dir)
        )
        print(f"Created package: {package_name}.zip")

def main():
    # Initialize generator
    generator = SocialMediaClipGenerator(
        source_video="/Users/cam/Desktop/video-automation/08 - GPT 5.0 This Summer.mp4",
        enhanced_audio="/Users/cam/Desktop/video-automation/08_gpt5_enhanced.wav",
        output_dir="/Users/cam/Desktop/video-automation/output_clips"
    )
    
    # Generate all clips
    results = generator.generate_all_clips()
    
    # Print summary
    print("\n=== CLIP GENERATION SUMMARY ===")
    successful_clips = [c for c in results['clips'] if 'error' not in c]
    failed_clips = [c for c in results['clips'] if 'error' in c]
    
    print(f"Total clips generated: {len(successful_clips)}")
    print(f"Failed clips: {len(failed_clips)}")
    
    if successful_clips:
        print("\nSuccessful clips:")
        for clip in successful_clips:
            print(f"- {clip['platform']}: {clip['filename']} ({clip['file_size_mb']} MB)")
    
    if failed_clips:
        print("\nFailed clips:")
        for clip in failed_clips:
            print(f"- {clip['platform']} ({clip['clip_id']}): {clip['error']}")
    
    # Create platform packages
    print("\nCreating platform packages...")
    for platform in ["tiktok", "youtube_shorts", "twitter", "linkedin"]:
        generator.generate_platform_package(platform)

if __name__ == "__main__":
    main()