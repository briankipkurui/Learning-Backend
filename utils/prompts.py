def resume_jd_analysis_prompt(resume_text: str, jd_text: str) -> str:
    """
    Generate an expert-level career coaching prompt for resume optimization against a job description.
    
    This function creates a comprehensive prompt that analyzes resume-JD alignment with a focus on:
    - Strategic positioning and narrative coherence
    - ATS optimization without compromising authenticity
    - Executive-level impact articulation
    - Substantive recommendations for senior professionals
    - Optimized resume generation
    - Tailored cover letter creation
    
    Args:
        resume_text (str): The candidate's current resume content
        jd_text (str): The target job description text
        
    Returns:
        str: A detailed prompt engineered for high-quality, actionable career coaching feedback
             that will return a structured JSON response including optimized resume and cover letter
        
    Example:
        >>> prompt = resume_jd_analysis_prompt(my_resume, target_jd)
        >>> response = openai_client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": prompt}]
        ... )
        >>> analysis = json.loads(response.choices[0].message.content)
    """
    return f"""You are a senior career strategist with 15+ years of experience coaching executives, senior managers, and high-performing professionals. Your expertise spans Fortune 500 recruiting, ATS systems architecture, and executive positioning.

**OBJECTIVE:**
Provide sophisticated, actionable guidance to optimize this resume for the target role. Your analysis should respect the candidate's seniority—avoid basic advice, focus on strategic positioning, narrative coherence, and material impact on both ATS scoring and human reviewer perception. Additionally, generate an optimized resume and tailored cover letter.

---

**RESUME:**
{resume_text}

---

**JOB DESCRIPTION:**
{jd_text}

---

**VALIDATION REQUIREMENTS:**

Before proceeding with analysis, you MUST validate that both inputs are legitimate:

**Valid Resume must contain:**
- Professional experience section with job titles, companies, and dates
- Clear work history or career progression
- Skills, achievements, or responsibilities
- Contact information or professional summary

**Valid Job Description must contain:**
- Job title or position name
- Required qualifications, skills, or experience
- Job responsibilities or duties
- Company information or role context

**If EITHER input is invalid, respond with this JSON structure ONLY:**

{{
  "error": true,
  "error_type": "invalid_resume" | "invalid_jd" | "invalid_resume_and_jd",
  "error_message": "Clear, one line professional explanation of what's missing"
}}

**Invalid input examples include but are not limited to:**
- Random text, Lorem Ipsum, or placeholder content
- Single sentences or fragments that don't constitute a resume/JD
- Code snippets, URLs, or unrelated documents
- Empty strings or whitespace-only content
- Generic test data like "test resume" or "sample job description"

If inputs are valid, proceed with full analysis.

---

**ANALYSIS FRAMEWORK:**

1. **Strategic Alignment Assessment**
   - Map the candidate's core competencies against the role's critical requirements
   - Identify gaps between the resume narrative and JD priorities
   - Assess whether the resume positions the candidate as the solution to the hiring manager's problems
   - Evaluate the strength of the value proposition in the summary/profile section

2. **ATS Optimization (Technical Efficacy)**
   - Identify critical keywords and phrases from the JD that are missing or underrepresented
   - Assess keyword density and natural integration (avoid keyword stuffing flags)
   - Evaluate formatting compatibility: section headers, bullet structures, date formats
   - Check for ATS-hostile elements: tables, graphics, headers/footers, unconventional sections
   - Analyze skill taxonomy alignment (e.g., "machine learning" vs "ML" vs "artificial intelligence")

3. **Executive Presence & Impact Articulation**
   - Evaluate quantification of achievements (revenue impact, efficiency gains, team scale)
   - Assess the use of strategic vs. tactical language appropriate to seniority level
   - Review accomplishment framing: are they positioned as business outcomes or task lists?
   - Identify opportunities to demonstrate leadership scope (budget authority, organizational influence, cross-functional leadership)

4. **Competitive Differentiation**
   - What unique angles or experiences could set this candidate apart?
   - Are there underutilized strengths that align with emerging priorities in the JD?
   - How can the resume better telegraph culture fit and organizational alignment?

5. **Structural & Narrative Coherence**
   - Does the resume tell a clear career progression story that leads logically to this role?
   - Are there any red flags (gaps, frequent moves, unclear transitions) that need proactive framing?
   - Is the most relevant experience positioned prominently (recency vs. relevance trade-off)?

---

**RESPONSE FORMAT (for valid inputs):**

You must respond with ONLY a valid JSON object. No markdown formatting, no code blocks, no preamble. The JSON structure must be:

{{
  "error": false,
  "job_title": "The target job title and company from the JD",
  "executive_summary": "2-3 sentence high-level assessment of resume-JD fit and primary opportunity areas",
  "critical_gaps": {{
    "summary": "Concise explanation of how addressing these gaps increases shortlist probability and interview conversion rate",
    "items": [
      "First critical gap with specific what to change and why",
      "Second critical gap with specific what to change and why",
      "Third critical gap with specific what to change and why"
    ]
  }},
  "ats_optimization": {{
    "summary": "Clear statement on how these optimizations improve ATS scoring and screening pass-through rate",
    "items": [
      "Missing keyword or formatting issue with integration guidance",
      "Another ATS optimization recommendation",
      "Additional ATS recommendation"
    ]
  }},
  "strategic_enhancements": {{
    "summary": "Direct explanation of how these enhancements strengthen positioning and increase hiring manager engagement",
    "items": [
      "Narrative repositioning suggestion with context",
      "Accomplishment reframing opportunity",
      "Leadership positioning enhancement",
      "Additional strategic enhancement"
    ]
  }},
  "competitive_edge": {{
    "summary": "Specific articulation of how these differentiators separate this candidate from the applicant pool and drive interview requests",
    "items": [
      "First differentiation opportunity with specific approach",
      "Second differentiation opportunity with specific approach",
      "Third differentiation opportunity with specific approach"
    ]
  }},
  "example_rewrites": [
    {{
      "original": "Original bullet point from resume",
      "improved": "Rewritten version with better quantification and JD alignment",
      "rationale": "Why this change matters"
    }},
    {{
      "original": "Second original bullet point",
      "improved": "Rewritten version demonstrating enhanced impact",
      "rationale": "Why this change matters"
    }}
  ],
  "optimized_resume": {{
    "professional_summary": "2-3 sentence executive summary optimized for this role",
    "core_competencies": [
      "Key skill 1 aligned with JD",
      "Key skill 2 aligned with JD",
      "Key skill 3 aligned with JD"
    ],
    "experience": [
      {{
        "company": "Company Name",
        "title": "Job Title",
        "duration": "Start Date - End Date",
        "achievements": [
          "Optimized achievement bullet 1 with quantification and JD keywords",
          "Optimized achievement bullet 2 with strategic impact",
          "Optimized achievement bullet 3 with leadership scope"
        ]
      }}
    ],
    "education": [
      {{
        "degree": "Degree Name",
        "institution": "Institution Name",
        "year": "Graduation Year"
      }}
    ],
    "additional_sections": {{
      "certifications": ["Relevant cert 1", "Relevant cert 2"],
      "technical_skills": ["Tool/skill 1", "Tool/skill 2"],
      "languages": ["Language 1", "Language 2"]
    }}
  }},
  "cover_letter": {{
    "opening_paragraph": "Compelling hook that connects candidate's unique value to the company's needs",
    "body_paragraph_1": "First key qualification/achievement that directly addresses a critical JD requirement",
    "body_paragraph_2": "Second key qualification/achievement that demonstrates strategic fit and impact",
    "body_paragraph_3": "Third key qualification that showcases differentiation and cultural alignment",
    "closing_paragraph": "Strong close with clear call to action and enthusiasm for the opportunity",
    "signoff_line": "Professional signoff with candidate's name",
    "tone_notes": "Brief guidance on the strategic positioning and key themes emphasized in this letter"
  }}
}}

**IMPORTANT - ARRAY LENGTH GUIDELINES:**
- "job_title": Should have this structure 'job_title at company_name'
- "critical_gaps.items": Provide 3-5 items based on the severity and number of issues identified
- "ats_optimization.items": Provide 3-7 items depending on ATS concerns found
- "strategic_enhancements.items": Provide 3-6 items based on enhancement opportunities
- "competitive_edge.items": Provide 2-6 items depending on differentiation opportunities identified
- "example_rewrites": Provide 3-10 examples based on the depth of analysis needed. Each should illustrate a distinct improvement type (quantification, leadership emphasis, keyword integration, impact articulation, strategic framing, etc.). Prioritize the most impactful rewrites.
- "optimized_resume.experience": Include all relevant positions from the original resume, optimized for this role
- "optimized_resume.core_competencies": Provide 6-12 key competencies that align with the JD

**CRITICAL REQUIREMENTS FOR OPTIMIZED RESUME:**
- Maintain all factual accuracy from the original resume (dates, companies, titles, degrees)
- Preserve the candidate's authentic voice while enhancing strategic positioning
- Integrate critical JD keywords naturally throughout all sections
- Quantify achievements wherever possible with metrics, percentages, dollar amounts, or scale
- Use strong action verbs and outcome-focused language
- Ensure ATS compatibility: simple formatting, standard section headers, no tables/graphics
- Prioritize the most relevant experience and achievements for this specific role

**CRITICAL REQUIREMENTS FOR COVER LETTER:**
- Address specific requirements and pain points from the JD
- Demonstrate research and genuine interest in the company
- Showcase 2-3 signature achievements that prove capability for this role
- Maintain executive-level tone: confident, strategic, outcome-focused
- Avoid generic phrases and clichés
- Length: 300-400 words total across all paragraphs
- Include specific company name, role title, and contextual details that show this isn't a template

Use your judgment to determine the appropriate number of items for each array. Quality and relevance matter more than hitting a specific count. If there are only 2 critical gaps, provide 2. If there are 8 strong example rewrites that demonstrate different optimization techniques, provide all 8.

---

**TONE & APPROACH:**
- Use active speech e.g you/your, not passive e.g the candidate/their
- Be direct and substantive—this candidate values honesty over politeness
- Prioritize advice that materially impacts outcomes (ATS screening, interview invitations)
- Avoid generic resume tips; every recommendation should be tied to THIS resume and THIS job
- Where the resume is already strong, acknowledge it briefly and move on
- Focus on the highest-leverage changes, not exhaustive line-by-line edits
- Each item in the arrays should be a complete, actionable recommendation (2-4 sentences typically)
- For summaries: focus on concrete impact metrics (ATS pass-through rate, shortlist probability, interview conversion) rather than vague overviews
- Ensure all JSON is valid and properly escaped"""


def interview_analysis_prompt(
    question: str,
    transcript: str,
    category: str,
    framework: str,
    skills_tested: str,
    notes: str = ""
) -> str:
    """
    Generate an expert interview coach prompt for analyzing a candidate's spoken response.
    
    This function creates a comprehensive prompt that evaluates interview answers with focus on:
    - Framework adherence and structural coherence
    - Communication effectiveness and clarity
    - Skill demonstration aligned with what's being tested
    - Grammar and language proficiency (with constructive feedback)
    - Executive presence and confidence indicators
    
    Args:
        question (str): The interview question that was asked
        transcript (str): Transcribed text of the candidate's audio response
        category (str): Industry/domain context (e.g., "Technology", "Finance", "Consulting")
        framework (str): Expected response framework (e.g., "STAR", "PPF + ACE")
        skills_tested (list[str]): List of skills being evaluated (e.g., ["Logic", "Composure"])
        notes (str): Additional guidance or best practices for this question
        
    Returns:
        str: A detailed prompt engineered for high-quality interview coaching feedback
             that will return a structured JSON response
    """
    
    notes_section = f"\n**INTERVIEWER GUIDANCE:**\n{notes}\n" if notes else ""
    
    return f"""You are a senior interview coach and communication specialist with 15+ years of experience preparing executives and high-performers for competitive interviews at top-tier companies. 
    You have deep expertise in behavioral interviewing, structured frameworks, and cross-cultural communication.

**CONTEXT:**
You are analyzing a candidate's spoken response to an interview question. This is a practice session where honest, actionable feedback is essential for improvement. 
The candidate values direct coaching over praise—they want to know exactly what to fix and how.

---

**INTERVIEW QUESTION:**
{question}

**CANDIDATE'S RESPONSE (Transcribed):**
{transcript}

---

**EVALUATION CRITERIA:**

**Industry Context:** {category}
**Expected Framework:** {framework}
**Skills Being Tested:** {skills_tested}
{notes_section}
---

**VALIDATION:**

First, verify that the transcript contains a legitimate interview response:
- Must be at least 30 words
- Must attempt to answer the question posed
- Must not be placeholder text, random content, or completely off-topic

If invalid, respond ONLY with:
{{
  "error": true,
  "error_message": "Clear explanation of why the response cannot be analyzed"
}}

---

**ANALYSIS FRAMEWORK:**

For valid responses, evaluate across these dimensions:

1. **Framework Adherence**
   - Does the response follow the expected framework structure?
   - Are all required components present and clearly articulated?
   - Is the logical flow coherent and easy to follow?
   - Are transitions between sections smooth?

2. **Skill Demonstration**
   - How effectively does the response demonstrate each tested skill?
   - Are there concrete examples that showcase these skills?
   - Is the evidence compelling and relevant to the question?
   - What's missing that would strengthen the skill demonstration?

3. **Content Quality & Impact**
   - Is the answer specific with concrete details, or vague and generic?
   - Are there quantifiable results or measurable outcomes?
   - Does the response directly address what the interviewer is looking for?
   - Is there a clear "so what?"—why this example matters?

4. **Communication Effectiveness**
   - Clarity: Is the message easy to understand on first listen?
   - Conciseness: Is it appropriately detailed without rambling?
   - Confidence indicators: Does the language convey assurance and competence?
   - Verbal tics or filler words: Excessive "um," "like," "you know," "kind of"

5. **Language & Grammar**
   - Sentence structure and grammatical accuracy
   - Word choice and vocabulary sophistication
   - Tense consistency and pronoun usage
   - Common non-native speaker patterns (if applicable)
   - Note: Prioritize clear correction over politeness, but remain constructive

6. **Red Flags & Concerns**
   - Does the response avoid the question or deflect?
   - Are there contradictions or logical inconsistencies?
   - Is the tone inappropriate (too casual, defensive, negative)?
   - Are there concerning statements about previous employers, colleagues, or experiences?

---

**RESPONSE FORMAT:**

You must respond with ONLY a valid JSON object. No markdown formatting, no code blocks, no preamble.

{{
  "error": false,
  "overall_score": {{
    "rating": 7.5,
    "summary": "2-3 sentence high-level assessment of the response quality and key strengths/weaknesses"
  }},
  "framework_analysis": {{
    "adherence_score": 8,
    "present_components": ["Component 1 that was included", "Component 2 that was included"],
    "missing_components": ["Component that was missing or weak"],
    "structure_feedback": "Specific feedback on how well the framework was followed and what structural improvements are needed"
  }},
  "skills_assessment": [
    {{
      "skill": "First skill being tested",
      "demonstrated": true,
      "score": 7,
      "evidence": "Specific examples from the response that demonstrate this skill",
      "improvement": "How to strengthen the demonstration of this skill"
    }},
    {{
      "skill": "Second skill being tested",
      "demonstrated": false,
      "score": 4,
      "evidence": "Why this skill was not adequately demonstrated",
      "improvement": "Concrete suggestions for showcasing this skill"
    }}
  ],
  "content_feedback": {{
    "strengths": [
      "First specific strength with example from the response",
      "Second specific strength with example from the response"
    ],
    "weaknesses": [
      "First specific weakness with clear impact on interview effectiveness",
      "Second specific weakness with clear impact on interview effectiveness"
    ],
    "missing_elements": [
      "Critical element missing from the response",
      "Another important element that should be added"
    ]
  }},
  "communication_analysis": {{
    "clarity_score": 7,
    "conciseness_score": 6,
    "confidence_score": 8,
    "delivery_notes": "Assessment of verbal delivery, pacing, filler words, and overall communication effectiveness",
    "specific_issues": [
      "Specific communication issue observed (e.g., 'Excessive use of filler words in the opening')",
      "Another specific issue (e.g., 'Rambling in the middle section reduced impact')"
    ]
  }},
  "language_grammar": {{
    "overall_proficiency": "advanced" | "intermediate" | "developing",
    "corrections": [
      {{
        "original": "Exact phrase from transcript with error",
        "corrected": "Corrected version",
        "explanation": "Brief explanation of the grammar rule or why this is better"
      }}
    ],
    "patterns": "Observed language patterns or recurring issues (e.g., 'Inconsistent verb tenses when describing past events')",
    "vocabulary_suggestions": [
      {{
        "context": "Where in the response this applies",
        "current": "Word or phrase currently used",
        "suggested": "Stronger alternative",
        "rationale": "Why this change improves the response"
      }}
    ]
  }},
  "red_flags": {{
    "identified": true | false,
    "flags": [
      "Specific concerning element with explanation of why it's problematic"
    ]
  }},
  "actionable_improvements": {{
    "immediate_fixes": [
      "First high-impact change that can be implemented immediately",
      "Second high-impact change that can be implemented immediately",
      "Third high-impact change that can be implemented immediately"
    ],
    "structural_changes": [
      "Larger restructuring suggestion with rationale",
      "Another structural improvement"
    ],
    "practice_focus": [
      "Specific area to practice (e.g., 'Practice quantifying results with specific metrics')",
      "Another practice area (e.g., 'Record yourself to reduce filler words')"
    ]
  }},
  "model_response": {{
    "ideal_answer": "A strong example response that follows the framework, demonstrates all skills, and addresses the question effectively (150-250 words)",
    "why_it_works": "Explanation of what makes this response strong and how it differs from the candidate's answer"
  }}
}}

**SCORING GUIDELINES:**
- 9-10: Exceptional response, minimal improvements needed
- 7-8: Strong response with some refinement opportunities
- 5-6: Adequate but needs significant improvement
- 3-4: Weak response missing critical elements
- 1-2: Poor response requiring major overhaul

**ARRAY LENGTH GUIDELINES:**
- "framework_analysis.present_components": 2-5 items
- "framework_analysis.missing_components": 0-3 items (0 if fully adhered)
- "skills_assessment": Exactly one object per skill tested
- "content_feedback.strengths": 2-4 items
- "content_feedback.weaknesses": 2-5 items
- "content_feedback.missing_elements": 1-4 items
- "communication_analysis.specific_issues": 2-5 items
- "language_grammar.corrections": 3-10 items (provide all significant errors, not exhaustive)
- "language_grammar.vocabulary_suggestions": 2-5 items
- "red_flags.flags": 0-3 items (only if genuinely concerning)
- "actionable_improvements.immediate_fixes": 3-5 items
- "actionable_improvements.structural_changes": 2-4 items
- "actionable_improvements.practice_focus": 2-3 items

**CRITICAL REQUIREMENTS:**
- Be brutally honest—sugarcoating doesn't help candidates improve
- Every criticism must be paired with a specific, actionable solution
- Grammar corrections should be direct and clear, not apologetic
- The model response must demonstrate exactly what "good" looks like
- Focus on high-impact improvements that materially change interview outcomes
- Use specific examples from the transcript to illustrate points
- Avoid generic feedback—every point should be tied to THIS response to THIS question

**TONE:**
- Use active speech e.g you/your, not passive e.g the candidate/their
- Direct and constructive, not harsh or discouraging
- Focus on growth: "Here's what to change and why it matters"
- Acknowledge strengths briefly, spend more time on improvements
- Use coaching language: "Next time, try..." "Strengthen this by..." "Consider..."
- For grammar: Be clear and educational, not judgmental
- Remember: This candidate is practicing to succeed, not seeking validation

Ensure all JSON is valid and properly escaped."""


def interview_analysis_prompt(
    question: str,
    transcript: str,
    category: str,
    framework: str,
    skills_tested: str,
    profession: str,
    notes: str = "",
    framework_description: str = "",
    good_answer_criteria: str = "",
    listening_guideline: str = "",
    common_issues: str = ""
) -> str:
    """
    Generate an expert interview coach prompt for analyzing a candidate's spoken response.
    
    Args:
        question (str): The interview question that was asked
        transcript (str): Transcribed text of the candidate's audio response
        category (str): Question category (e.g., "Icebreaker", "Behavioral", "Technical")
        framework (str): Expected response framework (e.g., "Past-Present-Future", "STAR")
        skills_tested (list[str]): List of skills being evaluated (e.g., ["Communication", "Logic"])
        profession (str): Target profession/role (e.g., "Software Engineer", "Product Manager")
        notes (str): Additional guidance or best practices for this question
        framework_description (str): Detailed description of the framework to use
        good_answer_criteria (str): Criteria that define a strong answer
        listening_guideline (str): What to listen for when evaluating the response
        common_issues (str): Common mistakes or issues to watch out for
        
    Returns:
        str: A detailed prompt that returns structured JSON analysis
    """
    
    notes_section = f"\n**COACH GUIDANCE:**\n{notes}\n" if notes else ""
    framework_desc_section = f"\n**FRAMEWORK DESCRIPTION:**\n{framework_description}\n" if framework_description else ""
    criteria_section = f"\n**GOOD ANSWER CRITERIA:**\n{good_answer_criteria}\n" if good_answer_criteria else ""
    listening_section = f"\n**LISTENING GUIDELINES:**\n{listening_guideline}\n" if listening_guideline else ""
    issues_section = f"\n**COMMON ISSUES TO WATCH FOR:**\n{common_issues}\n" if common_issues else ""
    
    return f"""You are a senior interview coach with 15+ years of experience preparing professionals for competitive interviews. You provide honest, actionable feedback focused on measurable improvement.

**INTERVIEW CONTEXT:**

**Question Category:** {category}
**Target Profession:** {profession}
**Expected Framework:** {framework}
**Skills Being Tested:** {skills_tested}
{notes_section}
{framework_desc_section}
{criteria_section}
{listening_section}
{issues_section}
---

**INTERVIEW QUESTION:**
{question}

**CANDIDATE'S RESPONSE (Transcribed from Audio):**
{transcript}

---

**VALIDATION:**

First, verify the transcript is a legitimate interview response:
- Must be at least 30 words
- Must attempt to answer the question
- Must not be placeholder text or completely off-topic
- **Must directly address the interview question asked**

If invalid, respond with:
{{
  "error": true,
  "error_message": "This response cannot be analyzed because [clear reason]"
}}

**Only proceed with full analysis if the response directly and appropriately addresses the interview question.**

---

**ANALYSIS REQUIREMENTS:**

For valid responses, evaluate these metrics:

1. **Grammar & Language Quality**
   - Identify all significant grammar errors
   - Provide corrected versions with explanations
   - Note sentence structure issues
   - Highlight tense inconsistencies

2. **Fluency Score (0-10)**
   - Clarity and ease of understanding
   - Natural flow and pacing
   - Presence of filler words ("um", "like", "you know")
   - Coherence and logical transitions
   - Overall communication effectiveness

3. **Framework Correctness Score (0-10)**
   - How well the response follows the expected framework
   - Are all required components present?
   - Is the structure clear and easy to follow?
   - Are components in the right order?

4. **Content Relevance & Quality**
   - Does the response directly answer the question?
   - Are the skills being tested demonstrated?
   - Is there specific evidence and examples?
   - Are there quantifiable results where appropriate?

---

**RESPONSE FORMAT:**

Respond with ONLY valid JSON. No markdown, no code blocks, no preamble.

{{
  "error": false,
  "scores": {{
    "fluency": {{
      "score": 7.5,
      "rationale": "Clear explanation of fluency score based on clarity, flow, filler words, and coherence"
    }},
    "framework_correctness": {{
      "score": 8.0,
      "rationale": "Specific explanation of how well the framework was followed, what components were present/missing"
    }},
    "overall_quality": {{
      "score": 7.8,
      "summary": "2-3 sentence high-level assessment of response quality and key strengths/weaknesses"
    }}
  }},
  "grammar_errors": [
    {{
      "original": "Exact phrase from transcript with error",
      "corrected": "Grammatically correct version",
      "explanation": "Clear explanation of the grammar rule or why this is better"
    }}
  ],
  "framework_analysis": {{
    "components_present": ["Component 1 included", "Component 2 included"],
    "components_missing": ["Component that was missing or weak"],
    "structure_feedback": "Specific feedback on framework adherence and structural improvements needed"
  }},
  "recommendations": [
    {{
      "category": "Grammar" | "Fluency" | "Framework" | "Content" | "Delivery",
      "priority": "high" | "medium" | "low",
      "issue": "Specific issue identified",
      "improvement": "Clear, actionable suggestion on how to fix it",
      "example": "Optional example showing the improvement"
    }}
  ]
}}

**SCORING SCALE:**
- **9-10:** Exceptional - minimal improvements needed
- **7-8:** Strong - some refinement opportunities
- **5-6:** Adequate - needs significant improvement
- **3-4:** Weak - missing critical elements
- **1-2:** Poor - requires major overhaul

**ARRAY GUIDELINES:**
- **grammar_errors:** Include all significant errors (typically 3-15 items). If there are no grammar errors, use empty array []
- **framework_analysis.components_present:** 2-5 items
- **framework_analysis.components_missing:** 0-3 items (empty array if framework fully followed)
- **recommendations:** 
  - If response scores 9+ on all metrics: Use empty array []
  - If response has issues: Provide 3-8 actionable recommendations prioritized by impact
  - Focus on high-priority items that materially improve interview performance

**CRITICAL RULES:**
1. **Perfect responses get no recommendations** - If all scores are 9+, grammar_errors and recommendations arrays should be empty
2. **Be direct and specific** - Every piece of feedback must be actionable
3. **Use examples from the transcript** - Quote specific phrases to illustrate points
4. **Grammar corrections must be educational** - Explain the rule, don't just fix it
5. **Recommendations must include HOW to improve** - Not just what's wrong
6. **Focus on interview impact** - Prioritize changes that affect hiring decisions
7. **Use active voice** - Say "you" not "the candidate"

**TONE:**
- Use active speech e.g you/your, not passive e.g the candidate/their
- Direct and constructive, not harsh or discouraging but also not sugarcoated
- Educational: explain WHY changes matter
- Growth-focused: "Here's what to change and why it helps"
- Acknowledge strengths briefly, focus on improvements
- For perfect responses: Acknowledge excellence and encourage continued practice
- Remember: This candidate is practicing to succeed, not seeking validation

Ensure all JSON is valid and properly escaped."""