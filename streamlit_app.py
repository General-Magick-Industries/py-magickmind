import streamlit as st
from libs.super_brain import SuperBrain
from libs.memories.episodic_memory import reflect, store_memory
from libs.memories.topic_track import track_topic_change
from typing import Dict, List

# Available models configuration
AVAILABLE_MODELS = {
    "GPT-4o": {
        "name": "openai/gpt-4o",
        "description": "Most capable model, best for complex tasks",
        "default": True
    },
    "Qwen2.5": {
        "name": "together_ai/qwen2.5",
        "description": "Good balance of speed and capability"
    },
    "Claude 3 Opus": {
        "name": "anthropic/claude-3-opus-20240229",
        "description": "Highly capable for analytical tasks"
    },
    "Claude 3.5 Sonnet": {
        "name": "anthropic/claude-3-5-sonnet-20240620",
        "description": "Fast and efficient for most tasks"
    }
}

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation' not in st.session_state:
        st.session_state.conversation = ""
    if 'iteration' not in st.session_state:
        st.session_state.iteration = 0
    if 'selected_models' not in st.session_state:
        # Default to first three models
        st.session_state.selected_models = list(AVAILABLE_MODELS.keys())[:3]

def setup_sidebar() -> tuple[List[str], int, int]:
    """Setup sidebar with model selection and chat controls"""
    st.sidebar.title("Settings")
    
    # Multiple model selection
    st.sidebar.subheader("Select Models")
    selected_models = st.sidebar.multiselect(
        "Choose models for thinking process (2-5 recommended)",
        options=list(AVAILABLE_MODELS.keys()),
        default=st.session_state.selected_models,
        format_func=lambda x: f"{x} ({AVAILABLE_MODELS[x]['description']})"
    )
    
    # Ensure at least one model is selected
    if not selected_models:
        st.sidebar.error("Please select at least one model")
        selected_models = [next(k for k, v in AVAILABLE_MODELS.items() if v.get('default', False))]
    
    st.session_state.selected_models = selected_models
    
    # Display selected models
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Selected Models")
    for model in selected_models:
        st.sidebar.markdown(f"- **{model}**: {AVAILABLE_MODELS[model]['description']}")
    
    # Add MCTS parameters
    st.sidebar.markdown("---")
    st.sidebar.markdown("### MCTS Parameters")
    iterations = st.sidebar.slider(
        "Number of Iterations",
        min_value=1,
        max_value=9,
        value=3,
        help="Higher values mean more thorough search but slower response"
    )
    
    max_depth = st.sidebar.slider(
        "Maximum Tree Depth",
        min_value=1,
        max_value=9,
        value=4,
        help="Higher values allow for more complex reasoning chains"
    )
    
    # Clear chat button
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation = ""
        st.session_state.iteration = 0
        st.rerun()
    
    # Convert selected models to their API names
    return [AVAILABLE_MODELS[model]["name"] for model in selected_models], iterations, max_depth

def display_chat_messages():
    """Display all messages in the chat"""
    # Create a container for messages
    messages_container = st.container()
    
    with messages_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]
            
            # Use the appropriate icon for each role
            if role == "user":
                with st.chat_message(role, avatar="🧑"):
                    st.write(content)
            else:
                with st.chat_message(role, avatar="🤖"):
                    st.write(content)

def process_user_message(user_message: str, small_brains: List[str], iterations: int, max_depth: int):
    """Process user message and generate response"""
    # Create a status message
    with st.status("Thinking...", expanded=True):
        super_brain = SuperBrain(include_semetic_memory=True)
        
        # Add user message to messages and conversation
        st.session_state.messages.append({"role": "user", "content": user_message})
        
        # Handle first message differently (no topic tracking)
        if st.session_state.iteration == 0:
            answer = super_brain.think(
                user_message, 
                small_brains=small_brains,
                iterations=iterations,
                max_depth=max_depth
            )
            st.session_state.conversation = f"User: {user_message}\nAssistant: {answer}"
        else:
            # Check for topic change and store memory if needed
            topic_change = track_topic_change(user_message, st.session_state.conversation)
            if topic_change:
                st.write("Topic change detected, updating memory...")
                reflection = reflect(st.session_state.conversation)
                store_memory(reflection, st.session_state.conversation)
            
            # Generate response
            answer = super_brain.think(
                user_message, 
                small_brains=small_brains,
                iterations=iterations,
                max_depth=max_depth
            )
            st.session_state.conversation += f"\nUser: {user_message}\nAssistant: {answer}"
        
        print(answer)
        # Add assistant response to messages
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.iteration += 1
        
    # Force a rerun to update the UI
    st.rerun()

def main():
    st.title("AI Chat Assistant")
    
    # Initialize session state
    initialize_session_state()
    
    # Setup sidebar and get parameters
    selected_model_names, iterations, max_depth = setup_sidebar()
    
    # Display chat interface
    st.markdown("---")
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input
    if user_message := st.chat_input("Type your message here..."):
        process_user_message(user_message, selected_model_names, iterations, max_depth)

if __name__ == "__main__":
    main()
