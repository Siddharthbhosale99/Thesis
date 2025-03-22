import re
import torch
import faiss
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer

# -----------------------------
# Load fine-tuned DialogPT model and tokenizer.
model_path = r"C:\Users\siddh\Downloads\Master Thesis\Chatbot 2\fine_tuned_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
model.eval()

# -----------------------------
def generate_response(prompt, context=None):
    input_text = prompt
    inputs = tokenizer.encode(input_text + tokenizer.eos_token, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=100,
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# -----------------------------
def personalize_with_username(response, context):
    username = context.get("user_name", "there")
    return response.replace("{user}", username)

# -----------------------------
def dynamic_category_response(category, input_text, context):
    prompt = f"User query regarding {category}: '{input_text}'. friendly response."
    response = generate_response(prompt, context)
    return personalize_with_username(response, context)

# -----------------------------
# A placeholder function for computing embeddings.

def compute_embedding(text):
    # For simplicity, we use the mean of token ids normalized into a vector.
    tokens = tokenizer.encode(text, add_special_tokens=False)
    if not tokens:
        return np.zeros(768, dtype='float32')
    vec = np.array(tokens, dtype='float32')
    embedding = np.mean(vec) * np.ones(768, dtype='float32')  
    return embedding

# -----------------------------
class DecisionTreeNode:
    def __init__(self, node_id, condition_func=None, response_template=None, children=None, personalization_func=None):
        self.node_id = node_id
        self.condition_func = condition_func
        self.response_template = response_template
        self.children = children if children is not None else []
        self.personalization_func = personalization_func

    def match(self, input_text, context):
        if self.condition_func is None:
            return True
        return self.condition_func(input_text, context)

    def get_response(self, input_text, context):
        if callable(self.response_template):
            response = self.response_template(input_text, context)
        elif self.response_template is not None:
            response = self.response_template
        else:
            response = generate_response(input_text, context)
        
        if self.personalization_func is not None:
            response = self.personalization_func(response, context)
        return response

# -----------------------------
class DecisionTreeProcessor:
    def __init__(self, root_node):
        self.root_node = root_node

    def traverse(self, input_text, context):
        return self._traverse_node(self.root_node, input_text, context)

    def _traverse_node(self, node, input_text, context):
        if node.match(input_text, context):
            for child in node.children:
                matched_child = self._traverse_node(child, input_text, context)
                if matched_child is not None:
                    return matched_child
            return node
        return None

# -----------------------------
def contains_keyword(keyword):
    def condition(input_text, context):
        return re.search(r'\b' + re.escape(keyword) + r'\b', input_text, re.IGNORECASE) is not None
    return condition

# -----------------------------
# Build decision tree using a predefined node order.
def build_decision_tree(node_order):
    root = DecisionTreeNode(
        node_id="root",
        response_template=None,
        children=[]
    )
    
    category_nodes = []
    for category in node_order:
        node = DecisionTreeNode(
            node_id=category,
            condition_func=contains_keyword(category),
            response_template=lambda input_text, context, cat=category: dynamic_category_response(cat, input_text, context)
        )
        category_nodes.append(node)
    
    fallback_node = DecisionTreeNode(
        node_id="fallback",
        condition_func=lambda input_text, context: True,
        response_template=lambda input_text, context: generate_response(input_text, context)
    )
    
    root.children.extend(category_nodes)
    root.children.append(fallback_node)
    return root

# -----------------------------
# FAISS Hybrid Search Component
class FAISSHybrid:
    def __init__(self, categories):
        self.categories = categories
        self.dim = 768  
        self.index = faiss.IndexFlatL2(self.dim)
        self.embeddings = []
        # Build index from category names
        for cat in categories:
            emb = compute_embedding(cat)
            self.embeddings.append(emb)
        self.embeddings = np.stack(self.embeddings)
        self.index.add(self.embeddings)  

    def search_category(self, input_text, k=1):
        query_emb = compute_embedding(input_text).reshape(1, -1)
        distances, indices = self.index.search(query_emb, k)
        # Return the best matching category
        best_index = indices[0][0]
        return self.categories[best_index]

# -----------------------------
# Updated processor that uses FAISS fallback if decision tree matching is too generic
class HybridDecisionTreeProcessor(DecisionTreeProcessor):
    def __init__(self, root_node, faiss_hybrid, threshold=1e6):
        super().__init__(root_node)
        self.faiss_hybrid = faiss_hybrid
        self.threshold = threshold  

    def traverse(self, input_text, context):
        # First, try the decision tree
        node = super().traverse(input_text, context)
        # If we hit the fallback node, we attempt FAISS-based matching
        if node.node_id == "fallback":
            matched_category = self.faiss_hybrid.search_category(input_text)
            # Build a temporary node using the matched category response
            temp_node = DecisionTreeNode(
                node_id=matched_category,
                response_template=lambda input_text, context, cat=matched_category: dynamic_category_response(cat, input_text, context)
            )
            return temp_node
        return node

# -----------------------------
def run_chatbot():
    context = {"user_name": "Alex"}
    default_order = [
        "shipping", "invoice", "cancellation", "subscription",
        "order_status", "payment_issue", "general_query",
        "refund", "technical_support", "feedback"
    ]
    decision_tree_root = build_decision_tree(default_order)
    # Initialize FAISS hybrid with the same categories used in the decision tree.
    faiss_hybrid = FAISSHybrid(default_order)
    processor = HybridDecisionTreeProcessor(decision_tree_root, faiss_hybrid)

    print("Chatbot is running. Type 'exit' to quit.")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Chatbot: Goodbye!")
            break

        matched_node = processor.traverse(user_input, context)
        if matched_node:
            response = matched_node.get_response(user_input, context)
        else:
            response = "I'm sorry, I didn't understand that."
        
        print("Chatbot:", response)

if __name__ == "__main__":
    run_chatbot()
