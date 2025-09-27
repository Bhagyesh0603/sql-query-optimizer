# query_explainer.py
import re
import difflib
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv

# Optional Gemini import
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Load environment variables
load_dotenv()

class QueryExplainer:
    def __init__(self):
        """Initialize the Query Explainer with Gemini API if available"""
        self.use_gemini = False
        if not GEMINI_AVAILABLE:
            print("⚠️ Google Gemini not available. Using built-in explanations.")
            return
            
        try:
            load_dotenv()
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                # Try multiple model versions in order of preference
                model_names = [
                    'models/gemini-2.0-flash',
                    'models/gemini-2.5-flash', 
                    'models/gemini-flash-latest',
                    'gemini-1.5-flash',
                    'gemini-1.5-pro',
                    'gemini-pro'
                ]
                
                for model_name in model_names:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        # Test the model with a simple call
                        test_response = self.model.generate_content("Test", 
                                                                 generation_config=genai.types.GenerationConfig(
                                                                     max_output_tokens=10,
                                                                     temperature=0.1
                                                                 ))
                        self.use_gemini = True
                        print(f"✅ Gemini API initialized with model: {model_name}")
                        break
                    except Exception as model_error:
                        print(f"⚠️ Model {model_name} failed: {str(model_error)[:100]}...")
                        continue
                
                if not self.use_gemini:
                    print("⚠️ No working Gemini models found. Using enhanced built-in explanations.")
                    print("💡 Tip: Check your API quota at https://console.cloud.google.com/")
            else:
                print("⚠️ No Gemini API key found. Using enhanced built-in explanations.")
        except Exception as e:
            print(f"⚠️ Gemini API not available: {e}. Using built-in explanations.")
    
    def explain_differences(self, original_query: str, optimized_query: str, 
                          optimization_type: str = "", performance_gain: str = "") -> str:
        """
        Explain the differences between original and optimized queries
        """
        if self.use_gemini:
            return self._explain_with_gemini(original_query, optimized_query, 
                                           optimization_type, performance_gain)
        else:
            return self._explain_built_in(original_query, optimized_query, 
                                        optimization_type, performance_gain)
    
    def _explain_with_gemini(self, original: str, optimized: str, 
                           opt_type: str, performance: str) -> str:
        """Use Gemini API to explain query differences"""
        try:
            prompt = f"""
            Analyze these SQL queries and provide a well-formatted technical explanation.

            📋 ORIGINAL QUERY:
            {original}

            ⚡ OPTIMIZED QUERY:
            {optimized}

            📊 PERFORMANCE GAIN: {performance}
            🔧 OPTIMIZATION TYPE: {opt_type}

            Please provide a detailed analysis with the following structure:

            ## 🎯 CHANGES MADE
            List the specific syntax differences between the queries.

            ## ⚡ PERFORMANCE BENEFITS
            Explain why these changes improve query performance.

            ## 🔬 DATABASE ENGINE MECHANICS
            Detail how the optimization works at the database engine level.

            ## ⚠️ TRADE-OFFS & CONSIDERATIONS
            Discuss any limitations, memory requirements, or scenarios where this might not be optimal.

            ## 💡 BEST PRACTICES
            Explain when and how to use this optimization effectively.

            Use clear headings, bullet points, and keep explanations concise but technical.
            """
            
            # Configure generation parameters for detailed responses
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=2000,  # Increased for detailed explanations
                temperature=0.2,         # Lower for more focused responses
                top_p=0.9,
                top_k=50
            )
            
            response = self.model.generate_content(
                prompt, 
                generation_config=generation_config
            )
            
            if response and hasattr(response, 'text') and response.text:
                # Format and clean the response
                formatted_response = self._format_gemini_response(response.text)
                return formatted_response
            else:
                print("⚠️ Gemini API returned empty response")
                return self._explain_built_in(original, optimized, opt_type, performance)
                
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print("⚠️ Gemini API quota exceeded - using enhanced built-in explanations")
                print("💡 Tip: Check your usage at https://aistudio.google.com/app/apikey")
            elif "404" in error_msg:
                print(f"⚠️ Gemini model not found: {error_msg[:150]}...")
            elif "API_KEY" in error_msg.upper():
                print("⚠️ Gemini API key issue")
            else:
                print(f"⚠️ Gemini API error: {error_msg[:150]}...")
            return self._explain_built_in(original, optimized, opt_type, performance)
    
    def _format_gemini_response(self, response_text: str) -> str:
        """Format and clean Gemini API response for better display"""
        # Clean up the response
        lines = response_text.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            # Skip empty lines at the start
            if not line.strip() and not formatted_lines:
                continue
            
            # Clean up markdown formatting
            line = line.replace('**', '')
            line = line.replace('*', '•')
            
            # Ensure proper spacing after headers
            if line.strip().startswith('##'):
                if formatted_lines and formatted_lines[-1].strip():
                    formatted_lines.append('')
                formatted_lines.append(line.strip())
                formatted_lines.append('')
            elif line.strip().startswith('•') or line.strip().startswith('-'):
                # Indent bullet points
                formatted_lines.append('  ' + line.strip())
            else:
                formatted_lines.append(line)
        
        # Join and clean up
        result = '\n'.join(formatted_lines)
        
        # Ensure it's not too long
        if len(result) > 3000:
            # Truncate but try to end at a complete sentence
            truncated = result[:2800]
            last_period = truncated.rfind('.')
            if last_period > 2000:
                result = truncated[:last_period + 1] + "\n\n[Response truncated for display]"
            else:
                result = truncated + "\n\n[Response truncated for display]"
        
        return result
    
    def _explain_built_in(self, original: str, optimized: str, 
                         opt_type: str, performance: str) -> str:
        """Built-in explanation system"""
        differences = self._find_differences(original, optimized)
        explanation = self._generate_explanation(differences, opt_type, performance)
        return explanation
    
    def _find_differences(self, original: str, optimized: str) -> Dict[str, List[str]]:
        """Find specific differences between queries"""
        differences = {
            'hints_added': [],
            'clauses_added': [],
            'clauses_modified': [],
            'structure_changes': []
        }
        
        # Check for hints
        hint_pattern = r'/\*\+\s*(\w+(?:\s+\w+)*)\s*\*/'
        original_hints = re.findall(hint_pattern, original)
        optimized_hints = re.findall(hint_pattern, optimized)
        
        new_hints = set(optimized_hints) - set(original_hints)
        if new_hints:
            differences['hints_added'] = list(new_hints)
        
        # Check for LIMIT clause
        if 'LIMIT' in optimized.upper() and 'LIMIT' not in original.upper():
            limit_match = re.search(r'LIMIT\s+(\d+)', optimized, re.IGNORECASE)
            if limit_match:
                differences['clauses_added'].append(f"LIMIT {limit_match.group(1)}")
        
        # Check for other structural changes
        if len(optimized.split()) != len(original.split()):
            differences['structure_changes'].append("Query structure modified")
        
        return differences
    
    def _generate_explanation(self, differences: Dict, opt_type: str, performance: str) -> str:
        """Generate comprehensive explanation based on detected differences"""
        explanation = "📊 QUERY OPTIMIZATION EXPLANATION\n"
        explanation += "=" * 50 + "\n\n"
        
        if differences['hints_added']:
            explanation += "🎯 HINT OPTIMIZATION:\n"
            for hint in differences['hints_added']:
                explanation += f"• Added /*+ {hint} */ hint\n"
                explanation += self._explain_hint(hint) + "\n"
        
        if differences['clauses_added']:
            explanation += "⚡ CLAUSE ADDITIONS:\n"
            for clause in differences['clauses_added']:
                explanation += f"• Added {clause}\n"
                explanation += self._explain_clause(clause) + "\n"
        
        if differences['structure_changes']:
            explanation += "🔧 STRUCTURAL CHANGES:\n"
            for change in differences['structure_changes']:
                explanation += f"• {change}\n"
        
        if performance:
            explanation += f"📈 PERFORMANCE IMPACT:\n"
            explanation += f"• {performance} performance improvement\n\n"
        
        explanation += "💡 WHY THIS OPTIMIZATION WORKS:\n"
        explanation += self._explain_optimization_rationale(differences)
        
        # Add technical details section
        explanation += "\n🔬 TECHNICAL DETAILS:\n"
        explanation += self._explain_technical_details(differences)
        
        # Add best practices section
        explanation += "\n📚 BEST PRACTICES:\n"
        explanation += self._explain_best_practices(differences)
        
        return explanation
    
    def _explain_hint(self, hint: str) -> str:
        """Explain specific database hints"""
        hint_explanations = {
            'USE_HASH': "Forces hash join algorithm. Optimal for larger datasets where one table fits in memory and the other is scanned sequentially.",
            'USE_NL': "Forces nested loop join. Best for small result sets or when one table is much smaller than the other.",
            'USE_MERGE': "Forces sort-merge join. Efficient when both tables are large and pre-sorted on join columns.",
            'INDEX': "Forces use of specific index. Ensures optimal index utilization for the query pattern."
        }
        
        for key, explanation in hint_explanations.items():
            if key in hint.upper():
                return f"  → {explanation}"
        
        return f"  → Database hint: {hint}"
    
    def _explain_clause(self, clause: str) -> str:
        """Explain specific SQL clauses that were added"""
        if clause.startswith('LIMIT'):
            limit_value = clause.split()[-1]
            return (f"  → Limits result set to top {limit_value} rows\n"
                   f"    • Enables Top-N optimization algorithm\n"
                   f"    • Reduces memory usage and improves response time\n"
                   f"    • Perfect for pagination and 'show top results' scenarios\n"
                   f"    • Database can stop processing once limit is reached")
        elif 'WHERE' in clause.upper():
            return (f"  → Adds filtering condition: {clause}\n"
                   f"    • Reduces rows processed by subsequent operations\n" 
                   f"    • Can utilize indexes for faster data access\n"
                   f"    • Applied early in query execution pipeline")
        elif 'INDEX' in clause.upper():
            return (f"  → Creates covering index: {clause}\n"
                   f"    • Speeds up data retrieval for this query pattern\n"
                   f"    • Eliminates need for table lookups\n"
                   f"    • Provides sorted data access")
        else:
            return f"  → Added clause: {clause}\n    • Improves query execution efficiency"
    
    def _explain_optimization_rationale(self, differences: Dict) -> str:
        """Explain why the optimization improves performance"""
        rationale = ""
        
        if differences['hints_added']:
            rationale += "• Join algorithm selection is crucial for query performance\n"
            rationale += "• The optimizer chose the most efficient join strategy based on data characteristics\n"
        
        if any('LIMIT' in clause for clause in differences['clauses_added']):
            rationale += "• LIMIT enables the database to use top-N sorting algorithms\n"
            rationale += "• Query can terminate early once the required number of rows is found\n"
            rationale += "• Significantly reduces memory and CPU usage for large result sets\n"
        
        if not rationale:
            rationale = "• Query structure was optimized for better execution plan generation\n"
        
        return rationale
    
    def _explain_technical_details(self, differences: Dict) -> str:
        """Provide technical details about the optimization"""
        details = ""
        
        if differences['hints_added']:
            details += "• Database hints override the query optimizer's default choice\n"
            details += "• Hash joins create in-memory hash tables for faster lookups\n"
            details += "• Most effective when one table is significantly smaller\n"
        
        if any('LIMIT' in clause for clause in differences['clauses_added']):
            details += "• LIMIT clause enables 'Top-N' heap sort algorithm\n"
            details += "• Database maintains only N rows in memory during sorting\n"
            details += "• Prevents full result set materialization before sorting\n"
            details += "• Memory usage: O(N) instead of O(total_rows)\n"
        
        if not details:
            details = "• Query execution plan was restructured for optimal performance\n"
        
        return details
    
    def _explain_best_practices(self, differences: Dict) -> str:
        """Explain best practices and when to use these optimizations"""
        practices = ""
        
        if differences['hints_added']:
            practices += "• Use hints sparingly - optimizer usually makes good choices\n"
            practices += "• Test hint effectiveness on production-like data volumes\n"
            practices += "• Monitor for plan regression when data distribution changes\n"
        
        if any('LIMIT' in clause for clause in differences['clauses_added']):
            practices += "• Always use LIMIT for paginated results or 'top-N' queries\n"
            practices += "• Combine with appropriate ORDER BY for deterministic results\n"
            practices += "• Consider indexed columns in ORDER BY for faster sorting\n"
        
        if not practices:
            practices = "• Regularly analyze query performance with EXPLAIN PLAN\n"
            practices += "• Keep statistics updated for optimal query plans\n"
        
        return practices
    
    def show_side_by_side_diff(self, original: str, optimized: str) -> str:
        """Show side-by-side comparison of queries"""
        original_lines = original.split('\n')
        optimized_lines = optimized.split('\n')
        
        diff = list(difflib.unified_diff(
            original_lines, optimized_lines,
            fromfile='Original Query', tofile='Optimized Query',
            lineterm=''
        ))
        
        if len(diff) <= 2:  # Only headers, no differences
            return "No structural differences found."
        
        return '\n'.join(diff)


def demo_explainer():
    """Demo function to test the explainer"""
    explainer = QueryExplainer()
    
    original = """SELECT p.Name, d.Name, COUNT(*) FROM Patients p 
                  JOIN Appointments a ON p.PatientID = a.PatientID 
                  JOIN Doctors d ON a.DoctorID = d.DoctorID 
                  GROUP BY p.Name, d.Name 
                  ORDER BY COUNT(*) DESC"""
    
    optimized = """SELECT /*+ USE_HASH */ p.Name, d.Name, COUNT(*) FROM Patients p 
                   JOIN Appointments a ON p.PatientID = a.PatientID 
                   JOIN Doctors d ON a.DoctorID = d.DoctorID 
                   GROUP BY p.Name, d.Name 
                   ORDER BY COUNT(*) DESC 
                   LIMIT 20"""
    
    explanation = explainer.explain_differences(original, optimized, 
                                               "Hash Join + Limit", "15% improvement")
    print(explanation)


if __name__ == "__main__":
    demo_explainer()