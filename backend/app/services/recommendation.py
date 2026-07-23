import json
import re
import logging
from typing import Dict, Any, List, Optional
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        # Multi-domain standard benchmarks across major career fields
        self.role_benchmarks = {
            "Business Analyst": [
                "requirements gathering", "brd", "frd", "user stories", "jira", "confluence",
                "tableau", "power bi", "process mapping", "gap analysis", "stakeholder management",
                "sql", "excel", "wireframing", "use cases", "data analysis"
            ],
            "HR & Talent Specialist": [
                "recruitment", "talent acquisition", "performance management", "onboarding",
                "hris", "employee relations", "sourcing", "compliance", "interviewing",
                "hr analytics", "compensation & benefits", "training & development"
            ],
            "Data Analyst & BI": [
                "sql", "python", "tableau", "power bi", "excel", "data visualization",
                "data modeling", "statistics", "a/b testing", "etl", "data cleaning", "reporting"
            ],
            "Product Manager": [
                "product strategy", "roadmap", "user research", "agile", "scrum", "jira",
                "prioritization", "kpis", "a/b testing", "wireframing", "stakeholder management",
                "product launch", "market research"
            ],
            "Marketing & Growth": [
                "seo", "sem", "content marketing", "google analytics", "hubspot", "social media",
                "email marketing", "lead generation", "market research", "copywriting", "campaign management",
                "a/b testing", "crm"
            ],
            "Financial Analyst": [
                "financial modeling", "budgeting", "forecasting", "excel", "financial analysis",
                "variance analysis", "auditing", "compliance", "sap", "cash flow", "valuation", "reporting"
            ],
            "Operations & Project Manager": [
                "project management", "pmp", "scrum", "agile", "risk management", "vendor management",
                "budgeting", "process improvement", "operations management", "jira", "resource allocation", "kpis"
            ],
            "Software & Systems Professional": [
                "python", "javascript", "sql", "git", "apis", "system design", "docker",
                "agile", "problem solving", "cloud", "code review", "ci/cd", "react"
            ]
        }

    def analyze_skill_gaps(self, candidate_skills: List[str]) -> Dict[str, Any]:
        """Compare candidate skills against industry standards to calculate matching/missing sets."""
        candidate_skills_lower = {s.lower().strip() for s in candidate_skills}
        analysis = {}

        for role, benchmark_skills in self.role_benchmarks.items():
            matches = [s for s in benchmark_skills if s in candidate_skills_lower]
            gaps = [s for s in benchmark_skills if s not in candidate_skills_lower]
            match_percentage = int((len(matches) / len(benchmark_skills)) * 100) if benchmark_skills else 0

            analysis[role] = {
                "match_percentage": match_percentage,
                "matching_skills": [s.title() for s in matches],
                "missing_skills": [s.title() for s in gaps]
            }

        return analysis

    def get_local_recommendations(self, gap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rules engine returning domain-specific recommendations without LLM queries."""
        # Find best matched role
        best_role = max(gap_analysis.items(), key=lambda x: x[1]["match_percentage"])
        role_name = best_role[0]

        certifications = []
        courses = []
        steps = []

        if "Business Analyst" in role_name:
            certifications = ["CBAP (Certified Business Analysis Professional)", "PMI-PBA (Professional in Business Analysis)"]
            courses = ["Business Analysis Fundamentals (Udemy)", "Data Analysis with Excel & SQL (Coursera)"]
            steps = [
                "Master drafting BRDs/FRDs and detailed user stories in Jira",
                "Build interactive executive dashboards using Tableau or Power BI",
                "Conduct stakeholder interviews and document end-to-end process workflows"
            ]
        elif "HR" in role_name:
            certifications = ["SHRM-CP (Society for Human Resource Management)", "PHR (Professional in Human Resources)"]
            courses = ["Strategic Human Resources (LinkedIn Learning)", "People Analytics Specialization (Coursera)"]
            steps = [
                "Implement structured behavioral interviewing rubrics and ATS funnels",
                "Optimize onboarding workflows and HRIS data tracking",
                "Develop data-driven employee retention and performance appraisal frameworks"
            ]
        elif "Data Analyst" in role_name:
            certifications = ["Google Data Analytics Professional Certificate", "Microsoft Certified: Power BI Analyst"]
            courses = ["SQL for Data Science (Coursera)", "Complete Python for Data Analysis (Udemy)"]
            steps = [
                "Master complex SQL queries (joins, CTEs, window functions)",
                "Create automated executive dashboards in Power BI or Tableau",
                "Perform statistical cohort analysis and A/B test evaluation"
            ]
        elif "Product" in role_name:
            certifications = ["Certified Scrum Product Owner (CSPO)", "Product Management Professional (PMP)"]
            courses = ["Become a Product Manager (Udemy)", "Digital Product Management (Coursera)"]
            steps = [
                "Define Product Requirement Documents (PRDs) with quantitative KPIs",
                "Conduct customer discovery interviews and map user journeys",
                "Prioritize backlog features using the RICE/Kano evaluation framework"
            ]
        elif "Marketing" in role_name:
            certifications = ["Google Analytics Certified", "HubSpot Inbound Marketing Certification"]
            courses = ["Digital Marketing Specialization (Coursera)", "SEO & Growth Hacking Masterclass"]
            steps = [
                "Optimize paid acquisition channels and landing page conversion rates",
                "Build automated email drip sequences and lead scoring models",
                "Run multi-variant A/B testing on user acquisition funnels"
            ]
        elif "Financial" in role_name:
            certifications = ["CFA (Chartered Financial Analyst)", "FMVA (Financial Modeling & Valuation Analyst)"]
            courses = ["Financial Modeling & Valuation (CFI)", "Advanced Excel for Finance (Coursera)"]
            steps = [
                "Build 3-statement financial models with DCF valuation assumptions",
                "Perform budget variance analysis and monthly executive reporting",
                "Automate financial data extraction and scenario sensitivity analysis"
            ]
        elif "Operations" in role_name:
            certifications = ["PMP (Project Management Professional)", "Certified ScrumMaster (CSM)"]
            courses = ["Google Project Management Certificate", "Operations Management (Coursera)"]
            steps = [
                "Establish project charters and Work Breakdown Structures (WBS)",
                "Mitigate operational risks and manage vendor SLAs effectively",
                "Implement Lean/Six-Sigma workflow process efficiency improvements"
            ]
        else:
            certifications = ["AWS Certified Developer - Associate", "Google Cloud Associate Engineer"]
            courses = ["System Design & Architecture (Educative)", "Full Stack Software Development"]
            steps = [
                "Design scalable REST/GraphQL APIs with optimized database schemas",
                "Containerize applications with Docker and automated test pipelines",
                "Implement robust CI/CD integration and cloud deployment"
            ]

        # Format roadmap
        roadmap = {
            "target_role": role_name,
            "skill_gap_summary": f"Your profile matches {best_role[1]['match_percentage']}% of standard skills for a {role_name}.",
            "steps": steps
        }

        return {
            "gap_analysis": gap_analysis,
            "roadmap": roadmap,
            "certifications": certifications,
            "courses": courses
        }

    async def get_gemini_recommendations(self, gap_analysis: Dict[str, Any], candidate_skills: List[str]) -> Dict[str, Any]:
        """Query Gemini to generate a highly detailed, personalized recommendation plan across any professional domain."""
        import google.generativeai as genai
        
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Find best matching role
        best_role = max(gap_analysis.items(), key=lambda x: x[1]["match_percentage"])
        role_name = best_role[0]

        prompt = f"""
        You are an expert career advisor and talent strategist. Analyze this candidate's profile across their professional domain and generate a tailored career roadmap to help them excel as a competitive {role_name}.
        
        Candidate's current skills: {', '.join(candidate_skills) if candidate_skills else 'General Professional Background'}
        Best matched target role / domain: {role_name}
        Skill gap analysis for this role:
        - Matching Skills: {', '.join(best_role[1]['matching_skills']) if best_role[1]['matching_skills'] else 'None detected'}
        - Missing Skills (Gaps): {', '.join(best_role[1]['missing_skills']) if best_role[1]['missing_skills'] else 'None'}

        Generate a response strictly formatted as a valid JSON object. Do not include any explanation or markdown formatting like ```json.
        
        The JSON object structure MUST be exactly:
        {{
            "gap_analysis": {{ ... }},
            "roadmap": {{
                "target_role": "{role_name}",
                "skill_gap_summary": "A concise paragraph summarizing their domain strengths and key areas for career advancement.",
                "steps": [
                    "Actionable domain-specific step 1",
                    "Actionable domain-specific step 2",
                    "Actionable domain-specific step 3"
                ]
            }},
            "certifications": [
                "Industry certification 1",
                "Industry certification 2"
            ],
            "courses": [
                "Online Course 1",
                "Online Course 2"
            ]
        }}
        """

        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            response_text = response.text.strip()

            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?\n", "", response_text)
                response_text = re.sub(r"\n```$", "", response_text)
                response_text = response_text.strip()

            parsed = json.loads(response_text)
            parsed["gap_analysis"] = gap_analysis
            return parsed
        except Exception as e:
            logger.error(f"Gemini recommendation query failed: {str(e)}. Falling back to local rules.")
            return self.get_local_recommendations(gap_analysis)

    async def get_recommendations(self, candidate_skills: List[str]) -> Dict[str, Any]:
        """Orchestrate recommendations: analyze gaps -> get local or LLM details."""
        gap_analysis = self.analyze_skill_gaps(candidate_skills)
        
        if settings.GEMINI_API_KEY:
            logger.info("Using LLM (Gemini) for custom career recommendations.")
            return await self.get_gemini_recommendations(gap_analysis, candidate_skills)
        else:
            logger.info("Gemini API key not found. Using local recommendations mapping.")
            return self.get_local_recommendations(gap_analysis)
