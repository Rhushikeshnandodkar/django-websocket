from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sentence_transformers import SentenceTransformer, util
import os
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Load the relevancy model (ensure it's globally accessible for efficiency)
rel_model = SentenceTransformer('all-MiniLM-L6-v2')
# Load model, tokenizer, and relevancy model globally
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "../app/models", "spam_detector_model.h5")
TOKENIZER_PATH = os.path.join(BASE_DIR, "../app/models", "tokenizer.pickle")

# Load the spam detection model
model = load_model(MODEL_PATH)

# Load the tokenizer
with open(TOKENIZER_PATH, 'rb') as handle:
    tokenizer = pickle.load(handle)

class RelevancyAPIView(APIView):
    def calculate_relevancy(self, content, messages):
        content_embedding = rel_model.encode(content, convert_to_tensor=True)
        question_embeddings = rel_model.encode([msg["question"] for msg in messages], convert_to_tensor=True)

        # Calculate cosine similarity
        relevancy_scores = util.pytorch_cos_sim(content_embedding, question_embeddings)

        scores = relevancy_scores.squeeze().tolist()
        results = [
            {"question": messages[i]["question"], "score": scores[i], "username": messages[i].get("username", "Anonymous")}
            for i in range(len(messages))
        ]
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def post(self, request):
        try:
            # Extract content and messages from the request
            content = request.data.get("content")
            messages = request.data.get("messages")

            if not content:
                return Response({"error": "Content is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not messages or not isinstance(messages, list):
                return Response({"error": "Messages should be a list of questions with optional usernames"}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate relevancy
            rel_results = self.calculate_relevancy(content, messages)

            # Split results into most_relevant and other_relevant
            response_data = {
                "most_relevant": rel_results[:15],
                "other_relevant": rel_results[15:]
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class SpamDetectionAPIView(APIView):
    def predict_spam(self, comment):
        # Tokenize and pad the comment
        comment_seq = tokenizer.texts_to_sequences([comment])
        comment_pad = pad_sequences(comment_seq, maxlen=100, padding='post')
        # Predict spam probability
        prediction = model.predict(comment_pad)[0][0]
        return "Spam" if prediction > 0.5 else "Not Spam"

    def post(self, request):
        try:
            # Get input data
            comment = request.data.get("comment")
            username = request.data.get("username", "Anonymous")  # Default username if not provided

            if not comment:
                return Response({"error": "Comment is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Predict spam or not spam
            tag = self.predict_spam(comment)

            # Response structure
            response_data = {
                "comment": comment,
                "username": username,
                "tag": tag
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
