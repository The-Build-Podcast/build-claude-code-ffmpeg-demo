#!/usr/bin/env python3
"""
Podcast Content Analysis Tool for identifying viral moments and engagement opportunities
"""
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class PodcastContentAnalyzer:
    def __init__(self):
        self.viral_keywords = {
            'prediction': 8,
            'breakthrough': 9,
            'revolution': 8,
            'game-changer': 9,
            'shocking': 9,
            'exclusive': 8,
            'first time': 8,
            'never before': 9,
            'groundbreaking': 8,
            'unprecedented': 9,
            'jaw-dropping': 9,
            'mind-blowing': 9,
            'secret': 8,
            'revealed': 8,
            'leaked': 9,
            'confirmed': 8,
            'billion': 7,
            'trillion': 8,
            'impossible': 8,
            'insane': 8
        }
        
        self.platform_requirements = {
            'tiktok': {'min_duration': 15, 'max_duration': 60, 'ideal_duration': 30},
            'youtube_shorts': {'min_duration': 15, 'max_duration': 60, 'ideal_duration': 45},
            'instagram_reels': {'min_duration': 15, 'max_duration': 90, 'ideal_duration': 30},
            'twitter': {'min_duration': 10, 'max_duration': 140, 'ideal_duration': 45},
            'linkedin': {'min_duration': 30, 'max_duration': 600, 'ideal_duration': 120}
        }

    def parse_timestamp(self, timestamp: str) -> float:
        """Convert HH:MM:SS.mmm to seconds"""
        parts = timestamp.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])

    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS.mmm format"""
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = td.total_seconds() % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def calculate_engagement_score(self, text: str, duration: float) -> Dict[str, Any]:
        """Calculate engagement score based on multiple factors"""
        text_lower = text.lower()
        
        # Base scores
        keyword_score = 0
        for keyword, weight in self.viral_keywords.items():
            if keyword in text_lower:
                keyword_score += weight
        
        # Normalize keyword score to 0-10
        keyword_score = min(keyword_score / 3, 10)
        
        # Duration score (prefer bite-sized content)
        if 15 <= duration <= 60:
            duration_score = 10
        elif 60 < duration <= 120:
            duration_score = 8
        elif duration < 15:
            duration_score = 5
        else:
            duration_score = 6
        
        # Check for various content types
        has_question = '?' in text
        has_exclamation = '!' in text
        has_numbers = bool(re.search(r'\d+', text))
        has_quote = '"' in text or "'" in text
        
        # Content type scores
        content_type_score = 0
        if has_question: content_type_score += 2
        if has_exclamation: content_type_score += 2
        if has_numbers: content_type_score += 3
        if has_quote: content_type_score += 3
        
        # Calculate final score
        final_score = (keyword_score * 0.4 + 
                      duration_score * 0.3 + 
                      content_type_score * 0.3)
        
        return {
            'overall_score': round(final_score, 1),
            'keyword_score': round(keyword_score, 1),
            'duration_score': duration_score,
            'content_type_score': content_type_score,
            'factors': {
                'has_viral_keywords': keyword_score > 0,
                'has_question': has_question,
                'has_exclamation': has_exclamation,
                'has_numbers': has_numbers,
                'has_quote': has_quote,
                'optimal_duration': 15 <= duration <= 60
            }
        }

    def identify_platform_suitability(self, duration: float, content_type: str) -> List[str]:
        """Determine which platforms are best suited for this content"""
        suitable_platforms = []
        
        for platform, reqs in self.platform_requirements.items():
            if reqs['min_duration'] <= duration <= reqs['max_duration']:
                suitability_score = 10 - abs(duration - reqs['ideal_duration']) / 10
                
                # Adjust based on content type
                if platform == 'linkedin' and content_type in ['educational', 'professional']:
                    suitability_score += 2
                elif platform in ['tiktok', 'instagram_reels'] and content_type in ['entertaining', 'shocking']:
                    suitability_score += 2
                elif platform == 'twitter' and content_type in ['news', 'controversial']:
                    suitability_score += 2
                
                if suitability_score >= 7:
                    suitable_platforms.append(platform)
        
        return suitable_platforms

    def classify_content_type(self, text: str) -> str:
        """Classify the type of content based on text analysis"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['predict', 'forecast', 'expect', 'will be', 'going to']):
            return 'prediction'
        elif any(word in text_lower for word in ['shocking', 'insane', 'unbelievable', 'crazy']):
            return 'shocking'
        elif any(word in text_lower for word in ['learn', 'understand', 'explain', 'how to']):
            return 'educational'
        elif any(word in text_lower for word in ['business', 'enterprise', 'professional', 'career']):
            return 'professional'
        elif any(word in text_lower for word in ['funny', 'hilarious', 'joke', 'laugh']):
            return 'entertaining'
        elif any(word in text_lower for word in ['controversial', 'debate', 'disagree', 'wrong']):
            return 'controversial'
        else:
            return 'general'

    def generate_clip_title(self, text: str, content_type: str) -> str:
        """Generate an engaging title for the clip"""
        # Extract key phrases
        if 'gpt' in text.lower() and '5' in text:
            base = "GPT-5.0"
        else:
            base = "AI"
        
        # Generate title based on content type
        title_templates = {
            'prediction': f"🔮 {base} Coming This Summer? Mind-Blowing Prediction",
            'shocking': f"🤯 The {base} News That Changes EVERYTHING",
            'educational': f"📚 What You NEED to Know About {base}",
            'professional': f"💼 How {base} Will Transform Your Career",
            'entertaining': f"😱 You Won't Believe This {base} Take",
            'controversial': f"⚡ The {base} Truth Nobody's Talking About",
            'general': f"🚀 Breaking: {base} Update You Can't Miss"
        }
        
        return title_templates.get(content_type, f"🎯 {base} - Must Watch Moment")

    def extract_key_moments(self, segments: List[Dict]) -> List[Dict]:
        """Extract and analyze key moments from transcript segments"""
        key_moments = []
        
        for i, segment in enumerate(segments):
            start_time = self.parse_timestamp(segment['start_time'])
            end_time = self.parse_timestamp(segment['end_time'])
            duration = end_time - start_time
            text = segment['text']
            
            # Skip placeholder text
            if '[Segment' in text or '[Speech segment' in text:
                continue
            
            # Analyze engagement potential
            engagement = self.calculate_engagement_score(text, duration)
            content_type = self.classify_content_type(text)
            platforms = self.identify_platform_suitability(duration, content_type)
            
            if engagement['overall_score'] >= 7:
                moment = {
                    'segment_index': i,
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration_seconds': round(duration, 2),
                    'text': text,
                    'speaker': segment.get('speaker', 'Unknown'),
                    'engagement_score': engagement,
                    'content_type': content_type,
                    'suitable_platforms': platforms,
                    'suggested_title': self.generate_clip_title(text, content_type),
                    'viral_potential': 'high' if engagement['overall_score'] >= 8.5 else 'medium'
                }
                key_moments.append(moment)
        
        # Sort by engagement score
        key_moments.sort(key=lambda x: x['engagement_score']['overall_score'], reverse=True)
        
        return key_moments

    def create_chapters(self, segments: List[Dict], target_chapter_length: int = 300) -> List[Dict]:
        """Create logical chapter breaks based on content and timing"""
        chapters = []
        current_chapter_start = 0
        current_chapter_segments = []
        
        for i, segment in enumerate(segments):
            current_chapter_segments.append(segment)
            
            # Check if we should create a new chapter
            current_time = self.parse_timestamp(segment['end_time'])
            chapter_duration = current_time - current_chapter_start
            
            # Create chapter if duration exceeds target or topic changes significantly
            if chapter_duration >= target_chapter_length or i == len(segments) - 1:
                chapter = {
                    'chapter_number': len(chapters) + 1,
                    'start_time': self.format_timestamp(current_chapter_start),
                    'end_time': segment['end_time'],
                    'duration_seconds': round(chapter_duration, 2),
                    'title': f"Chapter {len(chapters) + 1}: GPT-5.0 Insights",
                    'segment_count': len(current_chapter_segments),
                    'key_topics': ['GPT-5.0', 'AI predictions', 'Summer 2024']
                }
                chapters.append(chapter)
                
                # Reset for next chapter
                if i < len(segments) - 1:
                    current_chapter_start = self.parse_timestamp(segments[i + 1]['start_time'])
                    current_chapter_segments = []
        
        return chapters

    def extract_keywords_and_entities(self, segments: List[Dict]) -> Dict[str, List[str]]:
        """Extract SEO-relevant keywords and entities"""
        all_text = ' '.join([seg['text'] for seg in segments])
        
        # Common AI/Tech keywords to look for
        keywords = {
            'ai_models': ['GPT-5', 'GPT-5.0', 'GPT', 'ChatGPT', 'OpenAI', 'AI model'],
            'timeframes': ['summer', '2024', 'this year', 'soon', 'release date'],
            'features': ['multimodal', 'reasoning', 'capabilities', 'performance', 'breakthrough'],
            'impact': ['revolution', 'game-changer', 'disruption', 'transformation'],
            'technical': ['parameters', 'training', 'compute', 'architecture', 'benchmark'],
            'business': ['enterprise', 'API', 'pricing', 'competition', 'market']
        }
        
        found_keywords = {}
        for category, terms in keywords.items():
            found = [term for term in terms if term.lower() in all_text.lower()]
            if found:
                found_keywords[category] = found
        
        return found_keywords

    def generate_analysis_report(self, transcript_data: Dict) -> Dict:
        """Generate comprehensive analysis report"""
        segments = transcript_data.get('segments', [])
        metadata = transcript_data.get('metadata', {})
        
        # Extract various insights
        key_moments = self.extract_key_moments(segments)
        chapters = self.create_chapters(segments)
        keywords = self.extract_keywords_and_entities(segments)
        
        # Calculate overall metrics
        total_duration = self.parse_timestamp(metadata.get('duration', '00:00:00'))
        high_engagement_moments = [m for m in key_moments if m['engagement_score']['overall_score'] >= 8]
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'podcast_metadata': {
                'title': 'GPT-5.0 Predictions for This Summer',
                'duration': metadata.get('duration'),
                'duration_seconds': round(total_duration, 2),
                'speakers': metadata.get('speakers_detected', 0),
                'language': metadata.get('language', 'en')
            },
            'content_summary': {
                'total_segments': len(segments),
                'high_engagement_moments': len(high_engagement_moments),
                'viral_clips_identified': len([m for m in key_moments if m['viral_potential'] == 'high']),
                'recommended_clips': min(5, len(key_moments))
            },
            'viral_moments': key_moments[:10],  # Top 10 moments
            'platform_recommendations': {
                'tiktok': [m for m in key_moments if 'tiktok' in m['suitable_platforms']][:3],
                'youtube_shorts': [m for m in key_moments if 'youtube_shorts' in m['suitable_platforms']][:3],
                'twitter': [m for m in key_moments if 'twitter' in m['suitable_platforms']][:3],
                'linkedin': [m for m in key_moments if 'linkedin' in m['suitable_platforms']][:3]
            },
            'chapters': chapters,
            'seo_keywords': keywords,
            'content_themes': {
                'primary': 'GPT-5.0 release predictions',
                'secondary': ['AI advancement', 'Technology timeline', 'Industry impact'],
                'target_audience': ['AI enthusiasts', 'Tech professionals', 'Business leaders']
            }
        }
        
        return report

def main():
    # Load transcript
    transcript_path = "/Users/cam/Desktop/video-automation/08_gpt5_enhanced_transcript.json"
    
    with open(transcript_path, 'r') as f:
        transcript_data = json.load(f)
    
    # Initialize analyzer
    analyzer = PodcastContentAnalyzer()
    
    # Generate analysis
    print("Analyzing podcast content for viral moments...")
    analysis_report = analyzer.generate_analysis_report(transcript_data)
    
    # Save report
    output_path = "/Users/cam/Desktop/video-automation/content_analysis_report.json"
    with open(output_path, 'w') as f:
        json.dump(analysis_report, f, indent=2)
    
    print(f"\nAnalysis complete! Report saved to: {output_path}")
    
    # Print summary
    print("\n=== CONTENT ANALYSIS SUMMARY ===")
    print(f"Total Duration: {analysis_report['podcast_metadata']['duration']}")
    print(f"High Engagement Moments Found: {analysis_report['content_summary']['high_engagement_moments']}")
    print(f"Viral Clips Identified: {analysis_report['content_summary']['viral_clips_identified']}")
    
    print("\n=== TOP 3 VIRAL MOMENTS ===")
    for i, moment in enumerate(analysis_report['viral_moments'][:3], 1):
        print(f"\n{i}. [{moment['start_time']} - {moment['end_time']}]")
        print(f"   Score: {moment['engagement_score']['overall_score']}/10")
        print(f"   Type: {moment['content_type']}")
        print(f"   Platforms: {', '.join(moment['suitable_platforms'])}")
        print(f"   Title: {moment['suggested_title']}")

if __name__ == "__main__":
    main()