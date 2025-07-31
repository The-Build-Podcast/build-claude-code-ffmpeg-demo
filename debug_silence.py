#!/usr/bin/env python3
import subprocess

cmd = 'ffmpeg -i 08_gpt5_enhanced.wav -af "silencedetect=n=-18dB:d=0.2" -f null - 2>&1'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)