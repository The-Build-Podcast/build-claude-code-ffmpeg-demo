#!/usr/bin/env python3
import subprocess
import json
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Timestamp:
    seconds: float
    formatted: str
    frame_30fps: int
    frame_24fps: int
    frame_60fps: int
    
    @classmethod
    def from_seconds(cls, seconds: float):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs % 1) * 1000)
        
        formatted = f"{hours:02d}:{minutes:02d}:{int(secs):02d}.{milliseconds:03d}"
        
        return cls(
            seconds=seconds,
            formatted=formatted,
            frame_30fps=int(seconds * 30),
            frame_24fps=int(seconds * 24),
            frame_60fps=int(seconds * 60)
        )

def run_silence_detection(audio_file: str) -> List[Dict]:
    """Run comprehensive silence detection"""
    cmd = f'ffmpeg -i "{audio_file}" -af "silencedetect=n=-18dB:d=0.2" -f null - 2>&1'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    silence_periods = []
    lines = result.stderr.split('\n')
    
    start_time = None
    for line in lines:
        if 'silence_start:' in line:
            match = re.search(r'silence_start:\s*([\d.]+)', line)
            if match:
                start_time = float(match.group(1))
        elif 'silence_end:' in line and start_time is not None:
            match_end = re.search(r'silence_end:\s*([\d.]+)', line)
            match_duration = re.search(r'silence_duration:\s*([\d.]+)', line)
            if match_end:
                end_time = float(match_end.group(1))
                duration = float(match_duration.group(1)) if match_duration else (end_time - start_time)
                silence_periods.append({
                    'start': start_time,
                    'end': end_time,
                    'duration': duration
                })
                start_time = None
    
    return silence_periods

def analyze_full_audio(audio_file: str) -> Dict:
    """Perform comprehensive audio analysis"""
    
    # Get file info
    probe_cmd = f'ffprobe -v quiet -print_format json -show_format -show_streams "{audio_file}"'
    result = subprocess.run(probe_cmd, shell=True, capture_output=True, text=True)
    file_info = json.loads(result.stdout)
    
    duration = float(file_info['format']['duration'])
    sample_rate = int(file_info['streams'][0]['sample_rate'])
    
    # Get volume statistics
    volume_cmd = f'ffmpeg -i "{audio_file}" -af "volumedetect" -f null - 2>&1'
    result = subprocess.run(volume_cmd, shell=True, capture_output=True, text=True)
    
    mean_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', result.stderr)
    max_match = re.search(r'max_volume:\s*([-\d.]+)\s*dB', result.stderr)
    
    mean_volume = float(mean_match.group(1)) if mean_match else None
    max_volume = float(max_match.group(1)) if max_match else None
    
    return {
        'duration': duration,
        'sample_rate': sample_rate,
        'mean_volume': mean_volume,
        'max_volume': max_volume
    }

def identify_speech_segments(audio_file: str, silence_periods: List[Dict], total_duration: float) -> List[Dict]:
    """Identify speech segments based on silence periods"""
    
    segments = []
    
    # If no silence detected, assume entire file is speech
    if not silence_periods:
        segments.append({
            'segment_id': 'segment_001',
            'start_time': Timestamp.from_seconds(0.0),
            'end_time': Timestamp.from_seconds(total_duration),
            'duration': total_duration,
            'boundary_type': 'file_boundary',
            'confidence': 0.9
        })
        return segments
    
    # Sort silence periods by start time
    silence_periods.sort(key=lambda x: x['start'])
    
    # First speech segment (from beginning to first silence)
    if silence_periods[0]['start'] > 0.5:  # If there's speech at the beginning
        segments.append({
            'segment_id': 'segment_001',
            'start_time': Timestamp.from_seconds(0.0),
            'end_time': Timestamp.from_seconds(silence_periods[0]['start'] - 0.1),
            'duration': silence_periods[0]['start'] - 0.1,
            'boundary_type': 'natural_pause',
            'confidence': 0.95
        })
    
    # Speech segments between silences
    for i in range(len(silence_periods) - 1):
        current_silence_end = silence_periods[i]['end']
        next_silence_start = silence_periods[i + 1]['start']
        
        if next_silence_start - current_silence_end > 0.5:  # Significant speech duration
            segments.append({
                'segment_id': f'segment_{len(segments)+1:03d}',
                'start_time': Timestamp.from_seconds(current_silence_end + 0.1),
                'end_time': Timestamp.from_seconds(next_silence_start - 0.1),
                'duration': next_silence_start - current_silence_end - 0.2,
                'boundary_type': 'natural_pause',
                'confidence': 0.95
            })
    
    # Last speech segment (from last silence to end)
    last_silence = silence_periods[-1]
    if total_duration - last_silence['end'] > 0.5:
        segments.append({
            'segment_id': f'segment_{len(segments)+1:03d}',
            'start_time': Timestamp.from_seconds(last_silence['end'] + 0.1),
            'end_time': Timestamp.from_seconds(total_duration),
            'duration': total_duration - last_silence['end'] - 0.1,
            'boundary_type': 'file_boundary',
            'confidence': 0.9
        })
    
    return segments

def main():
    audio_file = "08_gpt5_enhanced.wav"
    
    print("Analyzing audio file...")
    audio_info = analyze_full_audio(audio_file)
    
    print(f"\nAudio File Information:")
    print(f"  Duration: {audio_info['duration']:.3f} seconds")
    print(f"  Sample Rate: {audio_info['sample_rate']} Hz")
    if audio_info['mean_volume'] is not None:
        print(f"  Mean Volume: {audio_info['mean_volume']:.1f} dB")
    if audio_info['max_volume'] is not None:
        print(f"  Max Volume: {audio_info['max_volume']:.1f} dB")
    
    print("\nDetecting silence periods...")
    silence_periods = run_silence_detection(audio_file)
    
    print(f"\nFound {len(silence_periods)} silence periods:")
    for i, silence in enumerate(silence_periods):
        print(f"  Silence {i+1}: {silence['start']:.3f}s - {silence['end']:.3f}s (duration: {silence['duration']:.3f}s)")
    
    print("\nIdentifying speech segments...")
    segments = identify_speech_segments(audio_file, silence_periods, audio_info['duration'])
    
    # Generate detailed report
    report = {
        'segments': [],
        'video_info': {
            'fps': 30.0,  # Assuming 30fps
            'total_frames': int(audio_info['duration'] * 30),
            'duration': f"{int(audio_info['duration']//60):02d}:{int(audio_info['duration']%60):02d}.{int((audio_info['duration']%1)*1000):03d}"
        },
        'analysis_notes': f"Enhanced audio analyzed. Silence threshold: -18dB, minimum duration: 0.2s. Mean volume: {audio_info['mean_volume']:.1f}dB" if audio_info['mean_volume'] else "Enhanced audio analyzed. Silence threshold: -18dB, minimum duration: 0.2s"
    }
    
    print(f"\nDetailed Segment Report:")
    print("="*80)
    
    for seg in segments:
        fade_in = 0.5 if seg['boundary_type'] == 'natural_pause' else 0.3
        fade_out = 0.5 if seg['boundary_type'] == 'natural_pause' else 0.3
        
        segment_data = {
            'segment_id': seg['segment_id'],
            'start_time': seg['start_time'].formatted,
            'end_time': seg['end_time'].formatted,
            'start_frame': seg['start_time'].frame_30fps,
            'end_frame': seg['end_time'].frame_30fps,
            'fade_in_duration': fade_in,
            'fade_out_duration': fade_out,
            'silence_padding': {
                'before': 0.1,
                'after': 0.1
            },
            'boundary_type': seg['boundary_type'],
            'confidence': seg['confidence']
        }
        
        report['segments'].append(segment_data)
        
        print(f"\n{seg['segment_id'].upper()}:")
        print(f"  Time Range: {seg['start_time'].formatted} - {seg['end_time'].formatted}")
        print(f"  Duration: {seg['duration']:.3f} seconds")
        print(f"  Frames (30fps): {seg['start_time'].frame_30fps} - {seg['end_time'].frame_30fps}")
        print(f"  Frames (24fps): {seg['start_time'].frame_24fps} - {seg['end_time'].frame_24fps}")
        print(f"  Frames (60fps): {seg['start_time'].frame_60fps} - {seg['end_time'].frame_60fps}")
        print(f"  Boundary Type: {seg['boundary_type']}")
        print(f"  Confidence: {seg['confidence']:.0%}")
        print(f"  Recommended Fades: In={fade_in}s, Out={fade_out}s")
    
    # Save JSON report
    import json
    with open('timestamp_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*80)
    print("JSON report saved to: timestamp_report.json")
    
    # Generate FFmpeg commands for extracting segments
    print("\nFFmpeg Commands for Segment Extraction:")
    print("-"*80)
    for seg in segments:
        cmd = f"ffmpeg -i {audio_file} -ss {seg['start_time'].seconds:.3f} -to {seg['end_time'].seconds:.3f} -c copy {seg['segment_id']}.wav"
        print(f"{seg['segment_id']}: {cmd}")

if __name__ == "__main__":
    main()