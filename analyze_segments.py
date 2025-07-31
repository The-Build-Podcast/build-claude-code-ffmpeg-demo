#!/usr/bin/env python3
import subprocess
import json
import re
from typing import List, Dict, Tuple

def analyze_audio_segments(audio_file: str, segment_duration: float = 0.5) -> List[Dict]:
    """Analyze audio file in segments to detect speech boundaries"""
    
    # Get audio duration
    duration_cmd = f'ffprobe -v quiet -print_format json -show_format "{audio_file}"'
    result = subprocess.run(duration_cmd, shell=True, capture_output=True, text=True)
    file_info = json.loads(result.stdout)
    total_duration = float(file_info['format']['duration'])
    
    segments = []
    current_time = 0.0
    
    while current_time < total_duration:
        end_time = min(current_time + segment_duration, total_duration)
        
        # Analyze RMS level for this segment
        cmd = f'ffmpeg -ss {current_time} -t {segment_duration} -i "{audio_file}" -af "volumedetect" -f null - 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Extract mean volume
        mean_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', result.stderr)
        max_match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
        
        mean_vol = float(mean_match.group(1)) if mean_match else -100
        max_vol = float(max_match.group(1)) if max_match else -100
        
        segments.append({
            'start': current_time,
            'end': end_time,
            'mean_volume': mean_vol,
            'max_volume': max_vol,
            'is_speech': mean_vol > -25 and max_vol > -15  # Adjusted threshold for enhanced audio
        })
        
        current_time = end_time
    
    return segments

def find_speech_boundaries(segments: List[Dict]) -> List[Dict]:
    """Find natural speech boundaries from segment analysis"""
    boundaries = []
    in_speech = False
    speech_start = None
    
    for i, seg in enumerate(segments):
        if seg['is_speech'] and not in_speech:
            # Speech starts
            in_speech = True
            speech_start = seg['start']
        elif not seg['is_speech'] and in_speech:
            # Speech ends
            in_speech = False
            if speech_start is not None:
                # Add some padding for natural boundaries
                start_with_pad = max(0, speech_start - 0.1)
                end_with_pad = seg['start'] + 0.1
                
                boundaries.append({
                    'start': start_with_pad,
                    'end': end_with_pad,
                    'duration': end_with_pad - start_with_pad
                })
    
    # Handle case where speech continues to end
    if in_speech and speech_start is not None:
        boundaries.append({
            'start': max(0, speech_start - 0.1),
            'end': segments[-1]['end'],
            'duration': segments[-1]['end'] - speech_start + 0.1
        })
    
    return boundaries

if __name__ == "__main__":
    audio_file = "08_gpt5_enhanced.wav"
    
    print("Analyzing audio segments...")
    segments = analyze_audio_segments(audio_file, segment_duration=0.25)
    
    print("\nFinding speech boundaries...")
    boundaries = find_speech_boundaries(segments)
    
    print(f"\nFound {len(boundaries)} speech segments:")
    for i, boundary in enumerate(boundaries):
        print(f"\nSegment {i+1}:")
        print(f"  Start: {boundary['start']:.3f}s")
        print(f"  End: {boundary['end']:.3f}s")
        print(f"  Duration: {boundary['duration']:.3f}s")
        print(f"  Start Frame (30fps): {int(boundary['start'] * 30)}")
        print(f"  End Frame (30fps): {int(boundary['end'] * 30)}")