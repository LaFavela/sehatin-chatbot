from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from decision import classify_input
from greetings import generate_greeting
from recomendation import ask_ai_recomendation
from consultation import ask_ai_consultation
from general_Information import ask_ai_general
from convert_to_json import convert_to_json

app = FastAPI()

class ChatInput(BaseModel):
    message: str
    name: Optional[str] = "User"
    activity_level: Optional[str] = "Jarang"
    age: Optional[int] = 25
    height: Optional[int] = 170
    weight: Optional[int] = 65
    gender: Optional[str] = "Pria"

@app.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    try:
        clasify_result = classify_input(chat_input.message)
        
        if clasify_result == "greetings":
            response = generate_greeting(chat_input.message, chat_input.name)
            return {"response": response, "type": "greeting"}
            
        elif clasify_result == "recommendation" or clasify_result == "rekomendasi":
            response = ask_ai_recomendation(
                chat_input.name, 
                chat_input.activity_level, 
                chat_input.weight, 
                chat_input.height, 
                chat_input.age, 
                chat_input.gender, 
                chat_input.message
            )
            return convert_to_json(response)
            
        elif clasify_result == "consultation" or clasify_result == "konsultasi":
            response = ask_ai_consultation(
                chat_input.name, 
                chat_input.activity_level, 
                chat_input.weight, 
                chat_input.height, 
                chat_input.age, 
                chat_input.gender, 
                chat_input.message
            )
            return {"response": response, "type": "consultation"}
            
        elif clasify_result == "general":
            response = ask_ai_general(chat_input.message)
            return {"response": response, "type": "general"}
            
        else:
            return {"response": "I didn't understand that. Can you rephrase?", "type": "unknown"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # print to console if it runs
    print("Starting FastAPI server...")
    # run the app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)