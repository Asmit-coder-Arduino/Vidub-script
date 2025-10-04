import streamlit as st
import os
import tempfile
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import speech_recognition as sr
from gtts import gTTS
import googletrans
from googletrans import Translator
from pydub import AudioSegment
from pydub.silence import split_on_silence
import numpy as np
import base64
from io import BytesIO
import time

# Set page configuration
st.set_page_config(
    page_title="Video Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize translator
translator = Translator()

def get_available_languages():
    """Get available languages for translation"""
    return googletrans.LANGUAGES

def extract_audio_from_video(video_path):
    """Extract audio from video file"""
    try:
        video_clip = VideoFileClip(video_path)
        audio_path = "temp_audio.wav"
        video_clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video_clip.close()
        return audio_path
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        return None

def transcribe_audio(audio_path):
    """Transcribe audio to text using speech recognition"""
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except Exception as e:
        st.error(f"Error in transcription: {str(e)}")
        return None

def split_audio_into_chunks(audio_path, chunk_length_ms=30000):
    """Split audio into chunks for better processing"""
    audio = AudioSegment.from_wav(audio_path)
    chunks = []
    
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunks.append(chunk)
    
    return chunks

def translate_text(text, target_language):
    """Translate text to target language"""
    try:
        translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        st.error(f"Error in translation: {str(e)}")
        return None

def text_to_speech(text, language_code, output_path):
    """Convert text to speech in target language"""
    try:
        tts = gTTS(text=text, lang=language_code, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        st.error(f"Error in text-to-speech: {str(e)}")
        return False

def get_language_code(language_name):
    """Get language code from language name"""
    languages = get_available_languages()
    for code, name in languages.items():
        if name.lower() == language_name.lower():
            return code
    return 'en'  # Default to English

def replace_audio_in_video(video_path, new_audio_path, output_path):
    """Replace audio in video with translated audio"""
    try:
        video_clip = VideoFileClip(video_path)
        new_audio = AudioFileClip(new_audio_path)
        
        # Ensure audio length matches video
        if new_audio.duration > video_clip.duration:
            new_audio = new_audio.subclip(0, video_clip.duration)
        
        # Set the new audio
        final_clip = video_clip.set_audio(new_audio)
        
        # Write output file
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        video_clip.close()
        new_audio.close()
        final_clip.close()
        
        return True
    except Exception as e:
        st.error(f"Error replacing audio: {str(e)}")
        return False

def get_video_duration(video_path):
    """Get duration of video file"""
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except:
        return 0

def main():
    st.title("🎬 Video Translator")
    st.markdown("Upload a video and translate its audio to different languages!")
    
    # Sidebar
    st.sidebar.header("Settings")
    
    # Language selection
    languages = get_available_languages()
    target_language = st.sidebar.selectbox(
        "Select Target Language",
        options=list(languages.values()),
        index=list(languages.values()).index('english')
    )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a video file", 
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
        help="Supported formats: MP4, AVI, MOV, MKV, WMV"
    )
    
    if uploaded_file is not None:
        # Display video info
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / (1024*1024):.2f} MB"
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Original Video")
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                video_path = tmp_file.name
            
            # Display original video
            st.video(video_path)
            st.write(file_details)
        
        with col2:
            st.write("Translated Video")
            
            if st.button("🚀 Translate Video", type="primary"):
                with st.spinner("Processing your video..."):
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Extract audio
                    status_text.text("Step 1/4: Extracting audio from video...")
                    audio_path = extract_audio_from_video(video_path)
                    progress_bar.progress(25)
                    
                    if audio_path:
                        # Step 2: Transcribe audio
                        status_text.text("Step 2/4: Transcribing audio to text...")
                        transcribed_text = transcribe_audio(audio_path)
                        progress_bar.progress(50)
                        
                        if transcribed_text:
                            st.info(f"**Transcribed Text:** {transcribed_text}")
                            
                            # Step 3: Translate text
                            status_text.text("Step 3/4: Translating text...")
                            language_code = get_language_code(target_language)
                            translated_text = translate_text(transcribed_text, language_code)
                            progress_bar.progress(75)
                            
                            if translated_text:
                                st.success(f"**Translated Text ({target_language}):** {translated_text}")
                                
                                # Step 4: Convert to speech and merge with video
                                status_text.text("Step 4/4: Generating translated audio and merging with video...")
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tmp:
                                    tts_success = text_to_speech(translated_text, language_code, audio_tmp.name)
                                
                                if tts_success:
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_tmp:
                                        merge_success = replace_audio_in_video(
                                            video_path, 
                                            audio_tmp.name, 
                                            output_tmp.name
                                        )
                                    
                                    if merge_success:
                                        progress_bar.progress(100)
                                        status_text.text("Translation complete!")
                                        
                                        # Display translated video
                                        with open(output_tmp.name, "rb") as f:
                                            video_bytes = f.read()
                                        
                                        st.video(video_bytes)
                                        
                                        # Download button
                                        st.download_button(
                                            label="📥 Download Translated Video",
                                            data=video_bytes,
                                            file_name=f"translated_{uploaded_file.name}",
                                            mime="video/mp4"
                                        )
                                        
                                        # Cleanup temporary files
                                        try:
                                            os.unlink(audio_path)
                                            os.unlink(audio_tmp.name)
                                            os.unlink(output_tmp.name)
                                        except:
                                            pass
                                    else:
                                        st.error("Failed to merge translated audio with video")
                                else:
                                    st.error("Failed to generate speech from translated text")
                            else:
                                st.error("Translation failed")
                        else:
                            st.error("Speech recognition failed. Please try again with clearer audio.")
                    else:
                        st.error("Failed to extract audio from video")
                    
                    # Cleanup
                    try:
                        os.unlink(video_path)
                    except:
                        pass

    else:
        # Show instructions when no file is uploaded
        st.info("👆 Please upload a video file to get started")
        
        # Features section
        st.markdown("""
        ## Features
        
        - 🎵 Extract audio from videos
        - 🔊 Automatic speech recognition
        - 🌍 Translate to 100+ languages
        - 🗣️ Text-to-speech conversion
        - 🎬 Merge translated audio with original video
        - 📥 Download final translated video
        
        ## Supported Languages
        
        Includes popular languages like:
        - English, Spanish, French, German, Chinese, Japanese, Korean
        - Hindi, Arabic, Russian, Portuguese, Italian, and many more!
        """)

    # Footer
    st.markdown("---")
    st.markdown(
        "Built with ❤️ using Streamlit | "
        "Note: Large videos may take longer to process"
    )

if __name__ == "__main__":
    main()
