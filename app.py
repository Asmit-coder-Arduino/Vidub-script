import streamlit as st
import os
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
import googletrans
from googletrans import Translator

# Set page configuration
st.set_page_config(
    page_title="Video Translator",
    page_icon="🎬",
    layout="wide"
)

def main():
    st.title("🎬 Simple Video Translator")
    st.markdown("Upload a video and provide text to translate!")
    
    # Language selection
    languages = {
        'en': 'English',
        'es': 'Spanish', 
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'hi': 'Hindi',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-cn': 'Chinese'
    }
    
    target_language = st.selectbox(
        "Select Target Language",
        options=list(languages.values())
    )
    
    # Get language code
    lang_code = [code for code, name in languages.items() if name == target_language][0]
    
    # Text input for manual translation
    text_to_translate = st.text_area(
        "Enter text to translate and add to video:",
        height=100,
        placeholder="Enter the text you want to translate and add as audio to the video..."
    )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a video file", 
        type=['mp4', 'avi', 'mov']
    )
    
    if uploaded_file and text_to_translate:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Original Video")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                video_path = tmp_file.name
            st.video(video_path)
        
        with col2:
            if st.button("🚀 Translate & Process Video"):
                with st.spinner("Processing..."):
                    try:
                        # Translate text
                        translator = Translator()
                        translated_text = translator.translate(text_to_translate, dest=lang_code).text
                        
                        st.info(f"**Translated Text:** {translated_text}")
                        
                        # Convert to speech
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tmp:
                            tts = gTTS(translated_text, lang=lang_code)
                            tts.save(audio_tmp.name)
                            
                            # Merge with video
                            video_clip = VideoFileClip(video_path)
                            audio_clip = AudioFileClip(audio_tmp.name)
                            
                            # Set audio duration to match video
                            if audio_clip.duration > video_clip.duration:
                                audio_clip = audio_clip.subclip(0, video_clip.duration)
                            
                            final_clip = video_clip.set_audio(audio_clip)
                            
                            # Save output
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_tmp:
                                final_clip.write_videofile(
                                    output_tmp.name,
                                    verbose=False,
                                    logger=None
                                )
                                
                                # Display result
                                with open(output_tmp.name, "rb") as f:
                                    video_bytes = f.read()
                                
                                st.video(video_bytes)
                                
                                # Download button
                                st.download_button(
                                    "📥 Download Translated Video",
                                    video_bytes,
                                    f"translated_{uploaded_file.name}",
                                    "video/mp4"
                                )
                            
                            # Cleanup
                            final_clip.close()
                            video_clip.close()
                            audio_clip.close()
                            os.unlink(audio_tmp.name)
                            os.unlink(output_tmp.name)
                            
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                
                # Cleanup original file
                os.unlink(video_path)

if __name__ == "__main__":
    main()
