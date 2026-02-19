
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class MentorMatchingSystem:
    def __init__(self):
        """
        Initializes the Mentor Matching System.
        """
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.mentors_df = None
        # Mentees are now passed at runtime, so we don't store them permanently
        self.mentor_vectors = None
        self.is_trained = False

    def load_mentors(self, mentors_data):
        """
        Loads mentor data into pandas DataFrame.
        
        Args:
            mentors_data (list): List of dictionaries containing mentor data.
        """
        self.mentors_df = pd.DataFrame(mentors_data)

    def _create_metadata(self, row):
        """
        Refinement: Weighting job_title and tools higher by repeating them.
        """
        tools = " ".join(row.get('tools', []))
        interests = " ".join(row.get('interests', []))
        job_title = row.get('job_title', '')
        bio = row.get('bio', '')
        
        # Repeating job_title and tools twice to increase their importance
        weighted_text = f"{job_title} {job_title} {tools} {tools} {interests} {bio}".lower()
        return weighted_text

    def train(self):
        """
        Preprocesses data and trains the TF-IDF vectorizer on Mentor data.
        """
        if self.mentors_df is None:
            raise ValueError("Mentor data not loaded. Call load_mentors() first.")

        # Create metadata field for mentors
        self.mentors_df['metadata'] = self.mentors_df.apply(self._create_metadata, axis=1)

        # Fit on mentor metadata
        # Note: In a real production system with new user input, 
        # we fit only on training corpus (mentors) or a large representative corpus.
        self.tfidf.fit(self.mentors_df['metadata'])

        # Transform mentor data to vectors
        self.mentor_vectors = self.tfidf.transform(self.mentors_df['metadata'])
        
        self.is_trained = True
        print("Model trained on mentor data.")

    def get_matches(self, mentee_data, top_n=3):
        """
        Finds the best mentor matches for a given mentee dictionary.

        Args:
            mentee_data (dict): Dictionary containing mentee profile (job_title, tools, etc.)
            top_n (int): Number of top matches to return.

        Returns:
            list: List of dictionaries containing matched mentor details and scores.
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        # Process the single mentee data
        mentee_metadata = self._create_metadata(mentee_data)
        mentee_vector = self.tfidf.transform([mentee_metadata])

        # Calculate cosine similarity with all mentors
        similarities = cosine_similarity(mentee_vector, self.mentor_vectors).flatten()

        # Apply business rules and constraints
        matches = []
        mentee_exp = mentee_data.get('years_of_experience', 0)
        mentee_field = mentee_data.get('field', '')

        for i, mentor in self.mentors_df.iterrows():
            score = similarities[i]

            # Rule 1: Mentor must have strictly more experience than the mentee
            if mentor['years_of_experience'] <= mentee_exp:
                score = 0

            # Rule 2: Field Alignment Boost (New Refinement)
            elif mentor['field'] == mentee_field:
                score *= 1.2
            
            # Rule 3: Boost score if significant experience gap (>= 5 years)
            elif (mentor['years_of_experience'] - mentee_exp) >= 5:
                score *= 1.1

            if score > 0:
                matches.append({
                    'user_id': mentor['user_id'],
                    'job_title': mentor['job_title'],
                    'field': mentor['field'],
                    'years_of_experience': mentor['years_of_experience'],
                    'match_score': round(float(score), 4),
                    'bio': mentor['bio'],
                    'tools': mentor['tools'],
                    'interests': mentor['interests']
                })

        # Sort by score descending
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches[:top_n]

    def get_related_tools(self, job_title=None):
        """Returns tools used by mentors with the specific job title (or all if None)."""
        if self.mentors_df is None: return []
        
        df = self.mentors_df
        if job_title:
            df = df[df['job_title'] == job_title]
            
        all_tools = set()
        for tools_list in df['tools']:
            all_tools.update(tools_list)
        return sorted(list(all_tools))

    def get_related_interests(self, job_title=None):
        """Returns interests of mentors with the specific job title (or all if None)."""
        if self.mentors_df is None: return []
        
        df = self.mentors_df
        if job_title:
             df = df[df['job_title'] == job_title]
             
        all_interests = set()
        for interests_list in df['interests']:
            all_interests.update(interests_list)
        return sorted(list(all_interests))

    def get_mentors(self, page=1, limit=10, role_filter=None, tool_filter=None, interest_filter=None):
        """
        Returns a paginated list of mentors with optional filtering.
        """
        if self.mentors_df is None: return [], 0
        
        df = self.mentors_df.copy()
        
        # Apply Filters
        if role_filter:
            df = df[df['job_title'] == role_filter]
        
        if tool_filter:
            # Check if any of the mentor's tools match the filter
            df = df[df['tools'].apply(lambda x: tool_filter in x)]
            
        if interest_filter:
             df = df[df['interests'].apply(lambda x: interest_filter in x)]
             
        # Pagination
        total_count = len(df)
        start = (page - 1) * limit
        end = start + limit
        
        sliced_df = df.iloc[start:end]
        
        # Convert to list of dicts
        mentors_list = sliced_df.to_dict('records')
        
        return mentors_list, total_count

    def get_all_job_titles(self):

        """Returns a sorted list of unique job titles available in the mentor dataset."""
        if self.mentors_df is None: return []
        return sorted(self.mentors_df['job_title'].unique().tolist())

    def get_all_tools(self):
        """Returns a sorted list of unique tools available in the mentor dataset."""
        return self.get_related_tools(job_title=None)

    def get_all_interests(self):
        """Returns a sorted list of unique interests available in the mentor dataset."""
        return self.get_related_interests(job_title=None)

# Example Usage
if __name__ == "__main__":
    # Load data from external JSON files
    try:
        with open('mentors.json', 'r') as f:
            mentors_data = json.load(f)
        with open('mentees.json', 'r') as f:
            mentees_data = json.load(f)
    except FileNotFoundError:
        print("Error: JSON files not found. Run 'python3 data_generator.py' first.")
        exit(1)
    
    # Initialize System
    matcher = MentorMatchingSystem()
    
    # Load Mentors Only
    print(f"Loading {len(mentors_data)} mentors...")
    matcher.load_mentors(mentors_data)
    
    # Train Model
    print("Training model...")
    matcher.train()
    
    # === Test 1: Helper Methods ===
    print("\n--- Helper Methods (for Frontend) ---")
    print(f"Example Job Titles: {matcher.get_all_job_titles()[:5]}")
    print(f"Example Tools: {matcher.get_all_tools()[:5]}")
    print(f"Example Interests: {matcher.get_all_interests()[:5]}")

    # === Test 2: Match a runtime mentee ===
    print("\n--- Matching Test ---")
    # Simulate a mentee coming from the frontend (dict only)
    sample_mentee = {
        "job_title": "Junior Backend Engineer",
        "tools": ["Python", "Django", "PostgreSQL"],
        "years_of_experience": 1,
        "interests": ["API Design", "Security"],
        "bio": "I want to learn how to build scalable APIs."
    }
    print(f"Finding matches for: {sample_mentee['job_title']}")
    
    matches = matcher.get_matches(sample_mentee)
    
    if not matches:
        print("No matches found matching criteria.")
    else:
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match['job_title']} (Exp: {match['years_of_experience']}y) - Score: {match['match_score']:.4f}")
            print(f"   Bio: {match['bio'][:100]}...")