import streamlit as st
import asyncio
import os
import pandas as pd
import re
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
import traceback
from rich import print
from rich_console import console
from rich.logging import RichHandler
# Load environment variables from .env file
load_dotenv()


logger = logging.getLogger(__name__)

# Import the agents we need
from agents.discovery import StakeholderIdentificationAgent
from agents.research import LegalResearchAgent
# Use the refactored content agent
from agents import ContentInventoryAgent, ContentCategorizationAgent, ContentQualityAssessmentAgent#, ContentGapAnalysisAgent
# from agents.content import ContentInventoryAgent, ContentGapAnalysisAgent, ContentClassificationAgent # Keep old import commented for reference if needed
from agents.guidance import GuidanceAgent, get_help_resources_info, get_help_content  # Import the GuidanceAgent and helper functions
from agents import PracticeAreaGapAgent, FormatGapAgent, MultilingualNeedsAgent, GapReportAssemblyAgent

# Create a synchronous wrapper for async functions
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Initialize session state variables if they don't exist
# Help chat variables
if 'guidance_agent' not in st.session_state:
    st.session_state.guidance_agent = GuidanceAgent()
if 'help_chat_history' not in st.session_state:
    st.session_state.help_chat_history = []
if 'help_chat_expanded' not in st.session_state:
    st.session_state.help_chat_expanded = False

# Phase 1 variables
if 'stakeholders_content' not in st.session_state:
    st.session_state.stakeholders_content = None
if 'platforms_content' not in st.session_state:
    st.session_state.platforms_content = None
if 'analytics_content' not in st.session_state:
    st.session_state.analytics_content = None
if 'compliance_content' not in st.session_state:
    st.session_state.compliance_content = None

# Phase 2 variables
if 'content_inventory' not in st.session_state:
    st.session_state.content_inventory = None
if 'content_inventory_list' not in st.session_state:
    st.session_state.content_inventory_list = []
if 'gap_analysis' not in st.session_state:
    st.session_state.gap_analysis = None
if 'phase' not in st.session_state:
    st.session_state.phase = 1  # Track current phase (1 or 2)

# Helper functions for Phase 1 workflow
async def process_stakeholders(company_info):
    stakeholder_agent = StakeholderIdentificationAgent()
    stakeholders_prompt = f"Based on the following information, identify and categorize all marketing stakeholders into internal and external groups: {company_info}"
    try:
        stakeholders = await stakeholder_agent.aprocess(stakeholders_prompt)
        if hasattr(stakeholders, 'content'):
            return stakeholders.content
        return str(stakeholders)
    except Exception as e:
        return f"Error processing stakeholders: {str(e)}"

async def process_platforms(platform_info):
    stakeholder_agent = StakeholderIdentificationAgent()
    platforms_prompt = f"Based on the following information, create a comprehensive inventory of all marketing platforms used by the firm: {platform_info}"
    try:
        platforms = await stakeholder_agent.aprocess(platforms_prompt)
        if hasattr(platforms, 'content'):
            return platforms.content
        return str(platforms)
    except Exception as e:
        return f"Error processing platforms: {str(e)}"

async def process_analytics(analytics_data):
    stakeholder_agent = StakeholderIdentificationAgent()
    analytics_prompt = f"Create a marketing metrics overview report based on the following analytics data. Include insights, trends, and areas for improvement:\n\n{analytics_data}"
    try:
        analytics_report = await stakeholder_agent.aprocess(analytics_prompt)
        if hasattr(analytics_report, 'content'):
            return analytics_report.content
        return str(analytics_report)
    except Exception as e:
        return f"Error processing analytics: {str(e)}"

async def process_compliance(marketing_content, provincial_guidelines_content=None):
    legal_researcher = LegalResearchAgent()

    try:
        # Get provincial guidelines if not provided
        if not provincial_guidelines_content:
            guidelines_prompt = "Summarize the current marketing and advertising rules for law firms in Ontario and British Columbia, especially focusing on any restrictions around terms like 'specialist', 'expert', guarantees, and testimonials."
            provincial_guidelines = await legal_researcher.aprocess(guidelines_prompt)
            if hasattr(provincial_guidelines, 'content'):
                provincial_guidelines_content = provincial_guidelines.content
            else:
                provincial_guidelines_content = str(provincial_guidelines)

        # Perform compliance check
        compliance_prompt = f"""
        Review this legal marketing content against Canadian provincial law society regulations:

        MARKETING CONTENT:
        {marketing_content}

        PROVINCIAL GUIDELINES:
        {provincial_guidelines_content}

        Please identify any potential compliance issues, their risk level, and suggested changes.
        """

        compliance_check = await legal_researcher.aprocess(compliance_prompt)
        if hasattr(compliance_check, 'content'):
            return compliance_check.content
        return str(compliance_check)
    except Exception as e:
        return f"Error processing compliance check: {str(e)}"

# Helper functions for Phase 2 workflow
async def process_content_inventory(content_data):
    content_agent = ContentInventoryAgent()
    # Use aprocess directly with a prompt designed to return properly structured JSON data
    prompt = f"""
    Create a detailed catalog of content items from the following information.
    Extract each content item with its title, type, platform, publish date, and other available metadata.

    CONTENT DATA:
    {content_data}

    IMPORTANT FORMATTING INSTRUCTIONS:
    - Return a valid JSON array of objects
    - Each object should represent one content item
    - Include fields like title, format, url, publication_date, etc.
    - Example format: [{{"title": "Blog post title", "format": "Blog Post", "url": "http://example.com", "publication_date": "2023-01-15"}}]
    - Ensure all array and object braces are properly closed
    - Do not include any text before or after the JSON array
    """
    # Get the response properly
    try:
        response = await content_agent.aprocess(prompt)

        # Handle different response types
        if hasattr(response, 'content'):
            # If response has content attribute (normal case)
            content = response.content
        else:
            # If response is the content itself
            content = str(response)

        # Parse the JSON response
        import json
        try:
            # Try to find JSON array in the content - sometimes the model adds explanations
            # Look for the first [ character and the last ] character
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx >= 0 and end_idx > start_idx:
                # Extract just the JSON array portion
                json_array = content[start_idx:end_idx]
                return json.loads(json_array)
            else:
                # If no array brackets found, try parsing the whole content
                return json.loads(content)
        except json.JSONDecodeError:
            # Create a fallback response with error details
            return [{
                "error": "Could not parse as JSON",
                "title": "JSON Parsing Error",
                "raw_response": content[:200] + "..." if len(content) > 200 else content
            }]
    except Exception as e:
        # Fallback in case of any other error
        return [{
            "error": "Could not process content inventory",
            "exception": str(e),
            "title": "Processing Error - Report to Developer",
            "description": "This could be due to API key issues or service unavailability"
        }]

async def categorize_content_item(content_item):
    content_agent = ContentCategorizationAgent()
    print("Debug: Content Item:")
    console.print_json(content_item)
    print(f"Debug: Content Item Type: {type(content_item)}")
    try:
        # Parse to a dictionary if it's a string
        if isinstance(content_item, str):
            try:
                content_data = json.loads(content_item)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}
        else:
            content_data = content_item
            print(f"Debug: Content Data: {content_data}")
            print(f"Debug: Content Data Type: {type(content_data)}")

        # Define the prompt for the agent's aprocess method
        categorization_prompt = f"""
        Categorize this content item by practice area, target audience, and format.
        Analyze the provided details to determine the most relevant categories.
        Add these categories as new fields (e.g., 'ai_practice_area', 'ai_audience', 'ai_format')
        to the original content item dictionary.
        Return the *complete, updated* content item as a single, valid JSON object.
        Do not include any explanatory text before or after the JSON object.

        CONTENT ITEM:
        {json.dumps(content_data, indent=2)}
        """
        print(f"Debug Prompt for aprocess: {categorization_prompt}")

        # Call the agent's main processing method
        response_obj = await content_agent.aprocess(categorization_prompt)

        # Extract and parse the response content
        if hasattr(response_obj, 'content'):
            response_content = response_obj.content
        else:
            # Handle cases where the response might be the string itself
            response_content = str(response_obj)

        try:
            # Attempt to parse the response content as JSON
            result_dict = json.loads(response_content)
            print(f"SUCCESSFUL RESPONSE PARSED: {result_dict}")
            return result_dict
        except json.JSONDecodeError:
            logger.error(f"Failed to parse categorization response as JSON: {response_content}", exc_info=True)
            return {"error": "AI response was not valid JSON", "raw_response": response_content}
        except Exception as e:
            # Catch other potential errors during parsing or processing
            logger.error(f"Error processing categorization response: {e}", exc_info=True)
            return {"error": f"Error processing AI response: {str(e)}"}

    except Exception as e:
        logger.error(f"Exception during categorize_content_item execution: {e}", exc_info=True)
        # Use a more specific error message if possible
        return {"error": f"Error during categorization process: {str(e)}"}

async def evaluate_content_quality(content_item):
    content_agent = ContentQualityAssessmentAgent()
    print(f"Debug: Evaluation Content Item: {content_item}")
    print(f"Debug: Evaluation Content Item Type: {type(content_item)}")

    try:
        # Parse to a dictionary if it's a string
        if isinstance(content_item, str):
            try:
                content_data = json.loads(content_item)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON format"}
        else:
            content_data = content_item
            print(f"Debug: Evaluation Content Data: {content_data}")
            print(f"Debug: Evaluation Content Data Type: {type(content_data)}")

        # Use aprocess with a tool routing prompt
        evaluation_prompt = f"""
        Evaluate this content item for quality, currency, and strategic alignment.
        Analyze the provided details to determine the most appropriate evaluations,
        scoring each of quality and strategic alignment between 1 - 5, with 1 being the lowest score and 5 being the higest,
        and labelling currency as either Up-To-Date, Needs Updating or Outdated.
        Add these evaluations as new fields (e.g., 'ai_quality_evaluation', 'ai_currency_evaluation', 'ai_strategic_alignment_evaluation')
        to the original content item dictionary.
        Return the *complete, updated* content item as a single, valid JSON object.
        Do not include any explanatory text before or after the JSON object.
        CONTENT ITEM:
        {json.dumps(content_data, indent=2)}
        """
        print(f"Debug Evaluation Prompt for aprocess: {evaluation_prompt}")
        # Assuming ContentQualityAgent has a tool like analyze_content_quality
        # If not, this needs adjustment based on the actual tools in ContentQualityAgent
        response_obj = await content_agent.aprocess(evaluation_prompt)

        if hasattr(response_obj, 'content'):
            response_content = response_obj.content
        else:
            # Handle cases where the response might be the string itself
            response_content = str(response_obj)

        try:
            # Attempt to parse the response content as JSON
            result_dict = json.loads(response_content)
            print(f"SUCCESSFUL RESPONSE PARSED: {result_dict}")
            return result_dict
        except json.JSONDecodeError:
            logger.error(f"Failed to parse evaluation response as JSON: {response_content}", exc_info=True)
            return {"error": "AI response was not valid JSON", "raw_response": response_content}
        except Exception as e:
            # Catch other potential errors during parsing or processing
            logger.error(f"Error processing evaluation response: {e}", exc_info=True)
            return {"error": f"Error processing AI response: {str(e)}"}

    except Exception as e:
        logger.error(f"Exception during evaluate_content_item execution: {e}", exc_info=True)
        # Use a more specific error message if possible
        return {"error": f"Error during evaluation process: {str(e)}"}


# Function to save reports
def save_all_reports():
    os.makedirs("outputs", exist_ok=True)

    # Save Phase 1 reports
    if st.session_state.stakeholders_content:
        with open("outputs/stakeholder_inventory.md", "w") as f:
            f.write(st.session_state.stakeholders_content)

    if st.session_state.platforms_content:
        with open("outputs/platform_inventory.md", "w") as f:
            f.write(st.session_state.platforms_content)

    if st.session_state.analytics_content:
        with open("outputs/analytics_report.md", "w") as f:
            f.write(st.session_state.analytics_content)

    if st.session_state.compliance_content:
        with open("outputs/compliance_notes.md", "w") as f:
            f.write(st.session_state.compliance_content)

    # Save Phase 2 reports
    if st.session_state.content_inventory is not None:
        try:
            # Save as CSV
            st.session_state.content_inventory.to_csv("outputs/content_inventory.csv", index=False)
            # Save raw JSON
            if 'content_inventory_list' in st.session_state and st.session_state.content_inventory_list:
                import json
                with open("outputs/content_inventory.json", "w") as f:
                    json.dump(st.session_state.content_inventory_list, f, indent=2)
        except Exception as e:
            st.error(f"Error saving content inventory: {str(e)}")

    if st.session_state.gap_analysis:
        with open("outputs/content_gap_analysis.md", "w") as f:
            f.write(st.session_state.gap_analysis)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

# Function to handle help chat interaction
def handle_help_message(query):
    # Get the current phase context and help resources
    current_phase = "discovery" if st.session_state.phase == 1 else "content_inventory"

    # Initialize chat thread ID if not already set
    if 'help_chat_thread_id' not in st.session_state:
        # Use a UUID to create a stable, unique thread ID
        import uuid
        st.session_state.help_chat_thread_id = f"help_chat_{str(uuid.uuid4())}"

    # Get relevant help resources to include in context
    try:
        # Get resources info for context - use standalone function instead of method on the agent
        resources_info = get_help_resources_info()
        resources_list = "\n".join([f"- {r['title']} (path: {r['path']})" for r in resources_info])

        # Find potential matching resources based on simple keyword matching
        import re
        keywords = re.findall(r'\b\w+\b', query.lower())
        potential_matches = []

        for resource in resources_info:
            # Check if any keyword is in the title
            if any(keyword in resource['title'].lower() for keyword in keywords):
                # Load the content for this potential match - use standalone function
                content = get_help_content(resource['path'])
                if content:
                    potential_matches.append({
                        "title": resource['title'],
                        "path": resource['path'],
                        "content": content[:1000] + ("..." if len(content) > 1000 else "")  # Truncate long content
                    })

                    # Limit to 2 potential matches to avoid overloading context
                    if len(potential_matches) >= 2:
                        break

        # Create message with context
        message = f"""
        USER QUERY: {query}

        CURRENT CONTEXT:
        - The user is in the {current_phase} phase of the Legal AI Marketing Assistant.
        - This is a legal marketing tool that helps law firms manage and improve their marketing content.

        AVAILABLE HELP RESOURCES:
        {resources_list}

        POTENTIAL RELEVANT RESOURCE CONTENT:
        {"" if not potential_matches else "Here are some resources that might be relevant:"}

        {
            "".join([f"--- {m['title']} ---\n{m['content']}\n\n" for m in potential_matches]) if potential_matches else "No exact matches found in resources. Please use your general knowledge about legal marketing applications to help."
        }

        Please provide helpful information based on these resources. If these resources don't contain the answer,
        provide general guidance based on your knowledge of legal marketing and software applications.
        """

        # Process through the agent's aprocess method with thread_id for conversation continuity
        response_obj = run_async(st.session_state.guidance_agent.aprocess(
            message=message,
            thread_id=st.session_state.help_chat_thread_id
        ))

        # Extract the actual response content
        if hasattr(response_obj, 'content'):
            response = response_obj.content
        else:
            response = str(response_obj)

    except Exception as e:
        # Handle errors gracefully
        print(f"Error in help chat: {str(e)}")
        response = "I apologize, but I encountered an error while trying to help. Please try again later or contact support."

    # Update chat history
    st.session_state.help_chat_history.append({"role": "user", "content": query})
    st.session_state.help_chat_history.append({"role": "assistant", "content": response})

# Streamlit App UI
st.title("Legal Marketing Discovery & Analysis")
# Try to load logo image, but continue if file doesn't exist
try:
    st.sidebar.image("llai/static/images/ll_logo.png", use_container_width=True)
except:
    st.sidebar.title("Legal Marketing AI")

# Phase selector
phases = ["Phase 1: Discovery", "Phase 2: Content Inventory & Gap Analysis"]
selected_phase = st.sidebar.selectbox("Select Phase:", phases, index=st.session_state.phase-1)
st.session_state.phase = 1 if selected_phase == phases[0] else 2

if st.session_state.phase == 1:
    st.sidebar.title("Phase 1 Workflow")
else:
    st.sidebar.title("Phase 2 Workflow")

# Navigation in sidebar - different options based on phase
if st.session_state.phase == 1:
    page = st.sidebar.radio(
        "Navigate to:",
        ["Home", "Stakeholders", "Platforms", "Analytics", "Compliance", "Reports", "Export"]
    )
else:
    page = st.sidebar.radio(
        "Navigate to:",
        ["Home", "Content Inventory", "Content Categorization", "Gap Analysis", "Reports", "Export"]
    )

# Add Help Chat to sidebar
st.sidebar.markdown("---")
with st.sidebar:
    with st.expander("Help Assistant", expanded=st.session_state.help_chat_expanded):
        st.markdown("### Need assistance?")

        # Display chat history
        for message in st.session_state.help_chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            else:
                st.markdown(f"**Assistant:** {message['content']}")

        # Input for new messages
        with st.form(key="help_chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask a question:", key="help_input")
            submit_button = st.form_submit_button("Send")

            if submit_button and user_input:
                handle_help_message(user_input)
                st.session_state.help_chat_expanded = True
                st.rerun()

    # Examples of questions user might ask
    with st.expander("Suggested questions"):
        st.markdown("""
        - How do I add content to the inventory?
        - What is a gap analysis?
        - Where are my saved files stored?
        - How do I check for compliance issues?
        """)

if page == "Home" and st.session_state.phase == 1:
    st.markdown("""
    # Welcome to Phase 1: Discovery & Preliminary Data Gathering

    This application guides you through the first phase of the Canadian legal marketing workflow:

    1. **Identify Key Stakeholders & Marketing Assets** - Catalog your team and platforms
    2. **Collect Marketing Performance Data** - Gather and analyze metrics
    3. **Set Initial Benchmarks** - Establish baselines and compliance checks

    Use the sidebar navigation to move through each step of the process.

    ## Getting Started

    1. Begin with the **Stakeholders** section to identify team members and roles
    2. Then move to **Platforms** to catalog your marketing channels
    3. Continue to **Analytics** to process performance data
    4. Check **Compliance** to identify potential regulatory issues
    5. Review all your results in the **Reports** section
    6. Finally, **Export** your data for future reference

    Let's get started by clicking on "Stakeholders" in the sidebar!
    """)

    # Show progress in sidebar if any sections are complete
    st.sidebar.markdown("### Progress")
    if st.session_state.stakeholders_content:
        st.sidebar.success("✓ Stakeholders Identified")
    if st.session_state.platforms_content:
        st.sidebar.success("✓ Platforms Inventoried")
    if st.session_state.analytics_content:
        st.sidebar.success("✓ Analytics Processed")
    if st.session_state.compliance_content:
        st.sidebar.success("✓ Compliance Checked")

elif page == "Home" and st.session_state.phase == 2:
    st.markdown("""
    # Welcome to Phase 2: Comprehensive Content Inventory & Gap Analysis

    This phase builds on the foundation of Phase 1 to help you:

    1. **Create a detailed catalog of all existing marketing content**
    2. **Categorize and evaluate content by practice area, audience, and format**
    3. **Identify gaps in your content coverage**
    4. **Develop strategic recommendations for content development**

    ## Getting Started

    1. Begin with the **Content Inventory** page to catalog all your marketing content
    2. Continue to **Content Categorization** to tag and evaluate content items
    3. Use **Gap Analysis** to identify content opportunities
    4. Review your results in the **Reports** section
    5. **Export** your data for implementation planning

    Let's get started by clicking on "Content Inventory" in the sidebar!
    """)

    # Show progress in sidebar for Phase 2
    st.sidebar.markdown("### Progress")
    if st.session_state.content_inventory is not None:
        st.sidebar.success("✓ Content Inventoried")
    if 'content_categorized' in st.session_state and st.session_state.content_categorized:
        st.sidebar.success("✓ Content Categorized")
    if st.session_state.gap_analysis:
        st.sidebar.success("✓ Gap Analysis Completed")

elif page == "Stakeholders":
    st.header("Stakeholder Identification")

    st.markdown("""
    Identify all team members involved in marketing (internal staff, external agencies).
    Provide a description of your marketing team structure below.
    """)

    # Example data for reference
    with st.expander("See example"):
        st.markdown("""
        ```
        Our mid-sized Canadian legal firm has an internal marketing team of 3 people:
        - Marketing Director (Sarah) - responsible for overall strategy
        - Content Manager (James) - manages content creation and calendar
        - Digital Marketing Specialist (Aisha) - handles website and social media

        We also work with two external agencies:
        - SEO Agency (DigitalLaw Partners) - handles our search optimization
        - PR Firm (Crestview Communications) - manages media relations
        ```
        """)

    # Input area for company info
    company_info = st.text_area("Describe your marketing team structure:", height=200)

    if st.button("Identify Stakeholders"):
        if company_info:
            with st.spinner("Analyzing stakeholders..."):
                stakeholders_content = run_async(process_stakeholders(company_info))
                st.session_state.stakeholders_content = stakeholders_content
                st.success("Stakeholders identified successfully!")
                st.markdown(stakeholders_content)
        else:
            st.error("Please enter information about your marketing team.")

elif page == "Platforms":
    st.header("Marketing Platform Inventory")

    st.markdown("""
    Gather links/access to all marketing platforms (website CMS, social media accounts, email marketing tools).
    Provide details about your marketing platforms below.
    """)

    # Example data for reference
    with st.expander("See example"):
        st.markdown("""
        ```
        Our marketing platforms include:
        - Website: WordPress-based site (lawyerdomain.ca)
        - Social Media: LinkedIn, Twitter, and Facebook pages
        - Email Marketing: Mailchimp account with 2,500 subscribers
        - Content Distribution: JD Supra and Lexology
        - CRM: Clio Grow for lead management
        ```
        """)

    # Input area for platform info
    platform_info = st.text_area("Describe your marketing platforms:", height=200)

    if st.button("Generate Platform Inventory"):
        if platform_info:
            with st.spinner("Cataloging platforms..."):
                platforms_content = run_async(process_platforms(platform_info))
                st.session_state.platforms_content = platforms_content
                st.success("Platform inventory created successfully!")
                st.markdown(platforms_content)
        else:
            st.error("Please enter information about your marketing platforms.")

elif page == "Analytics":
    st.header("Marketing Performance Data")

    st.markdown("""
    Collect marketing performance data across your channels.
    Enter your analytics information below.
    """)

    # Example data for reference
    with st.expander("See example"):
        st.markdown("""
        ```
        MARKETING ANALYTICS OVERVIEW:

        Website:
        - 4500 total sessions per month
        - 3200 unique users
        - 45.2% bounce rate
        - Top performing pages: Services page (1500 views), About Us (1200 views)

        Social Media (LinkedIn):
        - 1950 followers (growing by ~50/month)
        - 2.9% average engagement rate
        - 2800 impressions per month

        Email Marketing:
        - 5 campaigns sent
        - 22.3% open rate
        - 3.5% click rate
        ```
        """)

    # Input area for analytics data
    analytics_data = st.text_area("Enter your marketing analytics data:", height=300)

    if st.button("Analyze Performance Data"):
        if analytics_data:
            with st.spinner("Analyzing marketing data..."):
                analytics_content = run_async(process_analytics(analytics_data))
                st.session_state.analytics_content = analytics_content
                st.success("Analytics report generated successfully!")
                st.markdown(analytics_content)
        else:
            st.error("Please enter your marketing analytics data.")

elif page == "Compliance":
    st.header("Regulatory Compliance Check")

    st.markdown("""
    Check your marketing content against provincial law society rules.
    Enter your marketing content below to identify potential compliance issues.
    """)

    # Example data
    with st.expander("See example content"):
        st.markdown("""
        ```
        Our team of specialized legal experts has over 20 years of experience in corporate law.
        We guarantee successful outcomes for our clients and have the best track record in the province.
        Contact our specialists today for a free consultation.
        ```
        """)

    # Input area for marketing content
    marketing_content = st.text_area("Enter your marketing content to check:", height=200)

    use_custom_guidelines = st.checkbox("I want to provide custom provincial guidelines")

    provincial_guidelines_content = None
    if use_custom_guidelines:
        provincial_guidelines_content = st.text_area("Enter provincial law society guidelines:", height=200)

    if st.button("Check Compliance"):
        if marketing_content:
            with st.spinner("Checking compliance..."):
                compliance_content = run_async(process_compliance(marketing_content, provincial_guidelines_content))
                st.session_state.compliance_content = compliance_content
                st.success("Compliance check completed!")
                st.markdown(compliance_content)
        else:
            st.error("Please enter your marketing content.")

elif page == "Reports":
    st.header("Phase 1 Reports")

    # Display all generated reports
    tab1, tab2, tab3, tab4 = st.tabs(["Stakeholders", "Platforms", "Analytics", "Compliance"])

    with tab1:
        if st.session_state.stakeholders_content:
            st.markdown(st.session_state.stakeholders_content)
        else:
            st.info("No stakeholder data generated yet. Go to the Stakeholders page to create this report.")

    with tab2:
        if st.session_state.platforms_content:
            st.markdown(st.session_state.platforms_content)
        else:
            st.info("No platform inventory generated yet. Go to the Platforms page to create this report.")

    with tab3:
        if st.session_state.analytics_content:
            st.markdown(st.session_state.analytics_content)
        else:
            st.info("No analytics report generated yet. Go to the Analytics page to create this report.")

    with tab4:
        if st.session_state.compliance_content:
            st.markdown(st.session_state.compliance_content)
        else:
            st.info("No compliance check performed yet. Go to the Compliance page to create this report.")

elif page == "Export":
    st.header("Export Phase 1 Deliverables")

    # Check if reports exist to export
    reports_exist = any([
        st.session_state.stakeholders_content,
        st.session_state.platforms_content,
        st.session_state.analytics_content,
        st.session_state.compliance_content
    ])

    if reports_exist:
        st.markdown("""
        Export all generated reports to Markdown files in the 'outputs' directory.
        These files can be used for future reference and shared with your team.
        """)

        if st.button("Export All Reports"):
            timestamp = save_all_reports()
            st.success(f"All reports exported successfully at {timestamp}!")

            # Display file list
            st.markdown("### Exported Files:")
            exported_files = []
            if st.session_state.stakeholders_content:
                exported_files.append("outputs/stakeholder_inventory.md")
            if st.session_state.platforms_content:
                exported_files.append("outputs/platform_inventory.md")
            if st.session_state.analytics_content:
                exported_files.append("outputs/analytics_report.md")
            if st.session_state.compliance_content:
                exported_files.append("outputs/compliance_notes.md")

            for file in exported_files:
                st.markdown(f"- {file}")
    else:
        st.warning("No reports have been generated yet. Complete the previous steps before exporting.")

elif page == "Content Inventory":
    st.header("Content Inventory")

    st.markdown("""
    Create a detailed catalog of all existing marketing content.
    Enter information about your content pieces below, or upload a spreadsheet.
    """)


    st.subheader("Upload Existing Inventory")
    # Option to upload existing inventory
    uploaded_file = st.file_uploader("Upload existing content inventory (CSV or Excel)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                inventory_df = pd.read_csv(uploaded_file)
            else:
                inventory_df = pd.read_excel(uploaded_file)

            # Store in both session state variables for consistency
            st.session_state.content_inventory = inventory_df
            # Convert DataFrame to list of dictionaries for JSON storage
            st.session_state.content_inventory_list = inventory_df.to_dict('records')

            st.success("Content inventory loaded successfully!")
            st.dataframe(inventory_df)

            # Add save button for uploaded inventory
            if st.button("Save Uploaded Inventory"):
                try:
                    # Create outputs directory if it doesn't exist
                    os.makedirs("outputs", exist_ok=True)

                    # Save as CSV
                    inventory_df.to_csv("outputs/content_inventory.csv", index=False)

                    # Save as JSON
                    import json
                    with open("outputs/content_inventory.json", "w") as f:
                        json.dump(st.session_state.content_inventory_list, f, indent=2)

                    st.success("Uploaded inventory saved to outputs/content_inventory.csv and outputs/content_inventory.json")
                except Exception as e:
                    st.error(f"Error saving inventory: {str(e)}")
        except Exception as e:
            st.error(f"Error loading file: {str(e)}")

    st.subheader("Manual Content Entry")

    # Form for manually entering content items
    with st.form("content_form"):
        st.markdown("### Enter Content Item Details")

        title = st.text_input("Content Title")
        format_type = st.selectbox(
            "Content Format",
            ["Blog Post", "Article", "Practice Area Page", "Case Study", "Newsletter",
             "FAQ Page", "Video", "Podcast", "Webinar", "Guide", "Infographic", "Testimonial"]
        )

        practice_area = st.multiselect(
            "Related Practice Areas",
            ["Administrative Law", "Business/Corporate Law", "Civil Litigation",
             "Criminal Law", "Employment/Labor Law", "Estate Law", "Family Law",
             "Immigration Law", "Real Estate Law", "Tax Law", "Intellectual Property"]
        )

        platform = st.text_input("Platform/Location (e.g., website URL, social media)")
        audience = st.multiselect(
            "Target Audience",
            ["Potential Clients", "Existing Clients", "Referral Sources",
             "Other Lawyers", "Media", "General Public"]
        )

        publication_date = st.date_input("Publication Date")

        content_description = st.text_area("Content Description/Excerpt")

        submitted = st.form_submit_button("Add to Inventory")

        if submitted:
            if not title:
                st.error("Content Title is required")
            else:
                # Create content item dictionary
                content_item = {
                    "title": title,
                    "format": format_type,
                    "practice_area": ", ".join(practice_area),
                    "platform": platform,
                    "audience": ", ".join(audience),
                    "publication_date": publication_date.strftime("%Y-%m-%d"),
                    "description": content_description
                }

                # Add to inventory list
                if 'content_inventory_list' not in st.session_state:
                    st.session_state.content_inventory_list = []

                st.session_state.content_inventory_list.append(content_item)

                # Convert list to DataFrame for display
                st.session_state.content_inventory = pd.DataFrame(st.session_state.content_inventory_list)

                st.success(f"Added '{title}' to content inventory")

    # Display current inventory
    if st.session_state.content_inventory is not None:
        st.subheader("Current Content Inventory")
        st.dataframe(st.session_state.content_inventory)

        # Save button
        if st.button("Save Content Inventory"):
            try:
                # Create outputs directory if it doesn't exist
                os.makedirs("outputs", exist_ok=True)

                # Save as CSV
                st.session_state.content_inventory.to_csv("outputs/content_inventory.csv", index=False)

                # Save raw JSON
                import json
                with open("outputs/content_inventory.json", "w") as f:
                    json.dump(st.session_state.content_inventory_list, f, indent=2)

                st.success("Content inventory saved to outputs/content_inventory.csv and outputs/content_inventory.json")

                # Mark as categorized in session state for progress tracking
                st.session_state.content_categorized = True
            except Exception as e:
                st.error(f"Error saving inventory: {str(e)}")
    else:
        st.info("No content inventory created yet. Add content using the form above or upload an existing inventory.")

elif page == "Content Categorization":
    st.header("Content Categorization & Evaluation")

    if st.session_state.content_inventory is None:
        st.warning("No content inventory available. Please create a content inventory first.")
    else:

        content_categorization_agent = ContentCategorizationAgent()

        st.markdown("""
        Categorize and evaluate your content to prepare for gap analysis.
        This will help identify which practice areas, audiences, and formats
        are well-covered and where you have gaps.
        """)

        # Select a content item to categorize
        content_titles = st.session_state.content_inventory["title"].tolist()
        selected_title = st.selectbox("Select content to categorize/evaluate:", content_titles)

        # Get the selected content item
        selected_index = content_titles.index(selected_title)
        selected_item = st.session_state.content_inventory_list[selected_index]

        print(f"Debug: selected_item: {selected_item}")

        # Display the current categories
        st.subheader("Current Categories")

        # Format for display
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Content Details**")
            st.markdown(f"**Title:** {selected_item['title']}")
            st.markdown(f"**Format:** {selected_item['format']}")
            st.markdown(f"**Platform:** {selected_item['platform']}")
            if 'publication_date' in selected_item:
                st.markdown(f"**Publication Date:** {selected_item['publication_date']}")

        with col2:
            st.markdown("**Current Classifications**")
            if 'practice_area' in selected_item and selected_item['practice_area']:
                st.markdown(f"**Practice Areas:** {selected_item['practice_area']}")
            else:
                st.markdown("**Practice Areas:** *None assigned*")

            if 'audience' in selected_item and selected_item['audience']:
                st.markdown(f"**Target Audience:** {selected_item['audience']}")
            else:
                st.markdown("**Target Audience:** *None assigned*")

        # Actions
        st.subheader("Categorization Actions")

        with st.expander("Edit Categories Manually"):
            with st.form("categorize_form"):
                # Practice Areas
                practice_area = st.multiselect(
                    "Related Practice Areas",
                    ["Administrative Law", "Business/Corporate Law", "Civil Litigation",
                     "Criminal Law", "Employment/Labor Law", "Estate Law", "Family Law",
                     "Immigration Law", "Real Estate Law", "Tax Law", "Intellectual Property"],
                    default=selected_item.get('practice_area', '').split(', ') if selected_item.get('practice_area') else []
                )

                # Target Audience
                audience = st.multiselect(
                    "Target Audience",
                    ["Potential Clients", "Existing Clients", "Referral Sources",
                     "Other Lawyers", "Media", "General Public"],
                    default=selected_item.get('audience', '').split(', ') if selected_item.get('audience') else []
                )

                # Quality Metrics (New)
                st.markdown("### Quality Evaluation")
                quality_rating = st.slider("Content Quality Rating (1-5)", 1, 5, value=selected_item.get('quality_rating', 3))

                currency_status = st.selectbox(
                    "Content Currency Status",
                    ["Up-to-date", "Needs updating", "Outdated"],
                    index=0 if selected_item.get('currency_status') == "Up-to-date" else
                           1 if selected_item.get('currency_status') == "Needs updating" else
                           2 if selected_item.get('currency_status') == "Outdated" else 0
                )

                strategic_alignment = st.slider("Strategic Alignment (1-5)", 1, 5, value=selected_item.get('strategic_alignment', 3))

                update_submitted = st.form_submit_button("Update Categories")

                if update_submitted:
                    # Update the content item
                    st.session_state.content_inventory_list[selected_index]['practice_area'] = ', '.join(practice_area)
                    st.session_state.content_inventory_list[selected_index]['audience'] = ', '.join(audience)
                    st.session_state.content_inventory_list[selected_index]['quality_rating'] = quality_rating
                    st.session_state.content_inventory_list[selected_index]['currency_status'] = currency_status
                    st.session_state.content_inventory_list[selected_index]['strategic_alignment'] = strategic_alignment

                    # Update DataFrame
                    st.session_state.content_inventory = pd.DataFrame(st.session_state.content_inventory_list)

                    # Mark as categorized in session state for progress tracking
                    st.session_state.content_categorized = True

                    st.success(f"Updated categories for '{selected_title}'")
                    st.rerun()

        # Auto-categorize button
        if st.button("AI-Assisted Categorization"):
            with st.spinner("Analyzing content..."):
                # Prepare content item for categorization
                # categorization_input = json.dumps(selected_item)
                categorization_input = selected_item
                print(f"Debug: categorization_input: {categorization_input}")
                print(f"Debug: categorization_input type: {type(categorization_input)}")
                # Call categorization function using the helper
                # categorization_result = run_async(categorize_content_item(categorization_input)) # Pass the dict directly
                # categorization_result = asyncio.run(categorize_content_item(content_item=categorization_input)) # Pass the dict directly
                legal_taxonomy = [
  {
    "id": "administrative_law",
    "label": "Administrative Law",
    "description": "Regulation of government agencies and tribunals; oversight and remedies in public administration.",
    "subcategories": [
      "Alternative Dispute Resolution (Administrative Law)",
      "Boards / Agencies",
      "Citizenship (Administrative Law)",
      "Constitutional Law",
      "Coroners Inquests",
      "Criminal Injuries Compensation Board",
      "CRTC",
      "Customs",
      "Discipline & Fitness to Practice Hearings",
      "Education",
      "Human Rights / Discrimination (Administrative Law)",
      "Immigration (Administrative Law)",
      "Mental Health / Competency",
      "Military Law",
      "Municipal Law (Administrative Law)",
      "Native Law",
      "Police Complaints",
      "Privacy & Freedom of Information",
      "Social Program",
      "Transportation (Maritime) Law",
      "Transportation Law (Administrative Law)",
      "Workers' Compensation"
    ]
  },
  {
    "id": "business_law",
    "label": "Business / Corporate Law",
    "description": "Structures and operations of businesses, contracts, and regulatory compliance.",
    "subcategories": [
      "Alternative Dispute Resolution (Business Law)",
      "Bankruptcy and Insolvency Law",
      "Business Bankruptcy / Insolvency",
      "Business Leases",
      "Business Licensing and Zoning",
      "Business Purchase and Sale/ Lease",
      "Commercial Contract",
      "Computer Law",
      "Construction Law",
      "Copyright",
      "Directors Officers Duties",
      "e-Commerce Law",
      "Entertainment Law",
      "Environmental Law (Business Law)",
      "Farm Law",
      "Franchising / Licensing / Distribution Agreements",
      "Incorporations",
      "Independent Legal Advice (Business Law)",
      "Intellectual Property Protection",
      "International Business",
      "International Trade & NAFTA Disputes",
      "Mergers and Acquisitions",
      "Municipal / Zoning / By-law",
      "Non Profit Charitable Organizations / Corporations",
      "Partnership",
      "Patent",
      "Personal Property Security / Financing Security",
      "Provincial and Federal Corporate Law",
      "Publishing Contracts",
      "Securities Law",
      "Shareholder's Agreements",
      "Sports Law (Business Law)",
      "Tax Law",
      "Trademarks",
      "Transportation Law (Business Law)"
    ]
  },
  {
    "id": "civil_law",
    "label": "Civil Law",
    "description": "Legal disputes between individuals and organizations outside criminal prosecution.",
    "subcategories": [
      "Alternative Dispute Resolution (Civil Law",
      "Asbestos Mesothelioma Claims",
      "Aviation Law",
      "Chattel Leases / Liens",
      "Class Action",
      "Co-op Housing",
      "Commercial Landlord and Tenant",
      "Commercial Litigation",
      "Criminal Litigation",
      "Debt Collections",
      "Disability Law",
      "Education Litigation",
      "Environmental Law (Civil Law)",
      "Estate Litigation (Civil Law)",
      "Foreign Judgements, Decisions & Awards",
      "Human Rights / Discrimination (Civil Law)",
      "Injunctions",
      "Innkeepers Act",
      "Insurance Litigation",
      "Intellectual Property",
      "Lawyer Malpractice",
      "Medical Malpractice",
      "Mental Health (Civil Law)",
      "Motor Vehicle Accidents",
      "Municipal Law (Civil Law)",
      "Native Rights",
      "Personal Bankruptcy / Insolvency",
      "Personal Injury",
      "Product Liability",
      "Professional Malpractice",
      "Property Damage",
      "Real Estate Litigation (Civil Law)",
      "Residential Landlord and Tenant (Landlord)",
      "Residential Landlord and Tenant (Tenant)",
      "Slander / Libel",
      "Small Claims Court",
      "Solicitor-Client Assessments",
      "Tax Litigation",
      "Victims of Abuse (Civil Law)",
      "Wrongful Dismissal (Civil Law)"
    ]
  }
]
                categorization_result = content_categorization_agent.process(f"""I have the following 
                                                                             content that needs categorizing within
                                                                             a taxonomy:\nContent:\n{categorization_input}\nTaxonomy: {legal_taxonomy}""")

                print(f'Categorization Result: {categorization_result}')
                categorization_result = json.loads(categorization_result.content) # Convert to dict
                print(f'Categorization Result: {categorization_result}')

                # Process the result
                if isinstance(categorization_result, dict):
                    if 'error' in categorization_result:
                        st.error(f"AI Categorization Error: {categorization_result['error']}")
                        if 'raw_response' in categorization_result:
                            st.text_area("Raw AI Response:", categorization_result['raw_response'], height=100)
                    else:
                        # Successfully received categorized dictionary
                        st.success(f"AI categorization completed for '{selected_title}'")
                        st.markdown("Applying suggested categories...")

                        for key, value in categorization_result.items():
                            if key not in ['error', 'raw_response']:
                                # Update the content item with new categories
                                st.session_state.content_inventory_list[selected_index][key] = value

                        # Update DataFrame
                        st.session_state.content_inventory = pd.DataFrame(st.session_state.content_inventory_list)

                        # Mark as categorized in session state for progress tracking
                        st.session_state.content_categorized = True
                        st.rerun() # Rerun to show updated data in the UI
                else:
                    # Handle unexpected result type
                    st.error("Received unexpected result format from AI categorization.")
                    st.text(str(categorization_result))

        # Quality evaluation button
        if st.button("AI-Assisted Quality Evaluation"):
            with st.spinner("Evaluating content quality..."):
                # Prepare content item for evaluation
                # evaluation_input = json.dumps(selected_item)
                evaluation_input = selected_item
                print(f"Debug: categorization_input: {evaluation_input}")
                print(f"Debug: categorization_input type: {type(evaluation_input)}")
                evaluation_result = asyncio.run(evaluate_content_quality(content_item=evaluation_input))
                print(f'Categorization Result: {evaluation_result}')

                # Process the result
                if isinstance(evaluation_result, dict):
                    if 'error' in evaluation_result:
                        st.error(f"AI Evaluation Error: {evaluation_result['error']}")
                        if 'raw_response' in evaluation_result:
                            st.text_area("Raw AI Response:", evaluation_result['raw_response'], height=100)
                    else:
                        # Successfully received evaluated dictionary
                        st.success(f"AI evaluation completed for '{selected_title}'")
                        st.markdown("Applying evaluation results...")

                        # Update the content item with new/updated fields from the result
                        # We expect the AI to return the full item with added fields like 'ai_practice_area'
                        updated_item = evaluation_result
                        st.session_state.content_inventory_list[selected_index] = updated_item

                        # Update DataFrame
                        st.session_state.content_inventory = pd.DataFrame(st.session_state.content_inventory_list)


                        # Mark as evaluated in session state for progress tracking
                        st.session_state.content_evaluated = True
                        st.rerun() # Rerun to show updated data in the 
                        
                else:
                    # Handle unexpected result type
                    st.error("Received unexpected result format from AI evaluation.")
                    st.text(str(evaluation_result))


                

        # Save button
        if st.button("Save Categorized Inventory"):
            try:
                # Create outputs directory if it doesn't exist
                os.makedirs("outputs", exist_ok=True)

                # Save as CSV
                st.session_state.content_inventory.to_csv("outputs/categorized_content_inventory.csv", index=False)

                # Save raw JSON
                import json
                with open("outputs/content_inventory.json", "w") as f:
                    json.dump(st.session_state.content_inventory_list, f, indent=2)

                st.success("Categorized inventory saved to outputs/categorized_content_inventory.csv and outputs/content_inventory.json")
            except Exception as e:
                st.error(f"Error saving inventory: {str(e)}")

elif page == "Gap Analysis":
    st.header("Content Gap Analysis")

    if st.session_state.content_inventory is None:
        st.warning("No content inventory available. Please create a content inventory first.")
    else:
        # Instantiate the agent needed for this page
        # gap_agent = ContentGapAnalysisAgent()

        st.markdown("""
        Identify gaps in your content coverage based on practice areas, formats, and audiences.
        This analysis will help you develop a strategic content plan.
        """)

        st.subheader("Firm Information")
        st.markdown("Provide information about your firm to enable context-aware gap analysis.")

        # Firm information for gap analysis context
        with st.form("firm_info_form"):
            practice_areas = st.multiselect(
                "Select Your Firm's Practice Areas",
                ["Administrative Law", "Business/Corporate Law", "Civil Litigation",
                 "Criminal Law", "Employment/Labor Law", "Estate Law", "Family Law",
                 "Immigration Law", "Real Estate Law", "Tax Law", "Intellectual Property"]
            )

            english_pct = st.slider("Percentage of English-speaking clients (%)", 0, 100, 80)
            french_pct = st.slider("Percentage of French-speaking clients (%)", 0, 100, 20)

            other_languages = st.text_input("Other languages spoken by your clients (comma-separated)")

            primary_audience = st.multiselect(
                "Primary Target Audiences",
                ["Potential Clients", "Existing Clients", "Referral Sources",
                 "Other Lawyers", "Media", "General Public"]
            )

            strategic_focus = st.text_area("Current Strategic Focus Areas")

            firm_info_submitted = st.form_submit_button("Run Gap Analysis")

            if firm_info_submitted:
                if not practice_areas:
                    st.error("Please select at least one practice area")
                else:
                    # Format firm info for gap analysis
                    firm_info = f"""
                    Practice areas: {", ".join(practice_areas)}
                    Target audiences: {", ".join(primary_audience)}
                    {english_pct}% English-speaking clients
                    {french_pct}% French-speaking clients
                    Other languages: {other_languages}
                    Strategic focus: {strategic_focus}
                    """

                    # Run gap analysis using sequential agent calls
                    # Initialize results dictionary
                    analysis_results = {}
                    error_occurred = False

                    with st.spinner("Performing gap analysis (Step 1/4: Practice Areas)..."):
                        # try:
                        # --- Step 1: Identify Practice Area Gaps ---

                        # Get content inventory (ensure it's the list)
                        if 'content_inventory_list' not in st.session_state or not isinstance(st.session_state.content_inventory_list, list):
                            st.error("Content inventory list is not available or invalid in session state.")
                            # Stop execution if inventory is missing
                            raise ValueError("Content inventory list missing or invalid.")
                        
                        # print(f"Debug:session_state: {st.session_state}")
                        # print(f"Debug:content_inventory_list: {st.session_state.content_inventory_list}")

                        content_inventory_list = st.session_state.content_inventory_list
                        practice_areas_existing = [item['practice_area'] for item in content_inventory_list if 'practice_area' in item]
                        
                        print(f"Debug:practice_areas_existing: {practice_areas_existing}")    

                        st.write("Calling Practice Area Gaps tool...") # Debug message  

                        practice_area_gap_agent = PracticeAreaGapAgent()
                        # evaluation_result = asyncio.run(evaluate_content_quality(content_item=evaluation_input))
                        practice_area_gap_result_raw = practice_area_gap_agent.process(f"""I have the following 
                                                                                list of practice areas that currently exist in the content inventory 
                                                                                and a list of required practice areas that need comparing 
                                                                                to find areass that are requried but are not currently covered:\n
                                                                                  Covered:\n{practice_areas_existing}\nRequired: {practice_areas}""")

                        print("Debug:Practice Area Gaps Result:")
                        # console.print_json
                        # print(practice_area_gap_result_raw)
                        print(f'Debug:Practice Area Gaps Result Raw: {practice_area_gap_result_raw}')
                        practice_area_gap_result = practice_area_gap_result_raw.content # Convert to dict
                        print(f'Debug:Practice Area Gaps Result: {practice_area_gap_result}')


                        # Handle result/error
                        if isinstance(practice_area_gap_result, dict) and practice_area_gap_result.get("error"):
                            st.error(f"Error identifying practice area gaps: {practice_area_gap_result['error']}")
                            raise Exception(f"Practice area gap analysis failed: {practice_area_gap_result['error']}")
                        else:
                            st.write("Practice Area Gaps analysis successful.") # Debug message
                            # Store result for later use
                            analysis_results['practice_area_gaps'] = practice_area_gap_result
                            # print(f"Debug - Practice Gaps Result: {practice_area_gap_result}")

                        # except Exception as e:
                        #     st.error(f"Error during Practice Area Gap Analysis: {str(e)}")
                        #     error_occurred = True

                    # --- Step 2: Identify Format Gaps ---
                    if not error_occurred:
                        with st.spinner("Performing gap analysis (Step 2/4: Formats)..."):
                            try:
                                st.write("Calling Format Gaps tool...") # Debug message

                                format_gap_agent = FormatGapAgent()
                                # evaluation_result = asyncio.run(evaluate_content_quality(content_item=evaluation_input))

                                formats =  ["Blog Post", "Article", "Practice Area Page", "Case Study", "Newsletter",
                                "FAQ Page", "Video", "Podcast", "Webinar", "Guide", "Infographic", "Testimonial"]
                                formats_existing = [item['format'] for item in content_inventory_list if 'format' in item]

                                format_gaps_result_raw = format_gap_agent.process(f"""I have the following 
                                                                                list of content formats that exist in the content inventory
                                                                                and a list of required practice content formats that need comparing 
                                                                                to find formats that are requried but are not currently covered:
                                                                                Existing:\n{formats_existing}\nRequired: {formats}""")

                                print(f'Debug:Format Gaps Result Raw: {format_gaps_result_raw}')
                                format_gaps_result = format_gaps_result_raw.content
                                print("HERERERERERER")
                                print(f'Debug:Format Gaps Result Content: {format_gaps_result}')

                                
                                # Handle result/error
                                if isinstance(format_gaps_result, dict) and format_gaps_result.get("error"):
                                    st.error(f"Error identifying format gaps: {format_gaps_result['error']}")
                                    raise Exception(f"Format gap analysis failed: {format_gaps_result['error']}")
                                else:
                                    st.write("Format Gaps analysis successful.") # Debug message
                                    analysis_results['format_gaps'] = format_gaps_result
                                    print(f"Debug - Format Gaps Result: {format_gaps_result}")

                            except Exception as err:
                                traceback.print_exc()  # Print the full traceback for debugging
                                st.error(f"Error during Format Gap Analysis: {str(err)}")
                                
                                error_occurred = True

                    # # --- Step 3: Evaluate Multilingual Needs ---
                    # if not error_occurred:
                    #     with st.spinner("Performing gap analysis (Step 3/4: Languages)..."):
                    #         try:
                    #             # Prepare client_demographics input from firm_info
                    #             english_pct_match = re.search(r'(\d+)% English-speaking', firm_info)
                    #             french_pct_match = re.search(r'(\d+)% French-speaking', firm_info)
                    #             client_demographics = {"languages": {}}
                    #             if english_pct_match:
                    #                 client_demographics["languages"]["English"] = int(english_pct_match.group(1))
                    #             if french_pct_match:
                    #                 client_demographics["languages"]["French"] = int(french_pct_match.group(1))
                    #             other_langs_match = re.search(r'Other languages: ([^\\n]+)', firm_info)
                    #             if other_langs_match and other_langs_match.group(1).strip():
                    #                 client_demographics["languages"]["Other"] = other_langs_match.group(1).strip()

                    #             st.write("Calling Multilingual Needs tool...") # Debug message
                    #             multilingual_result = run_async(
                    #                 gap_agent.evaluate_multilingual_needs(
                    #                     content_inventory=content_inventory_list,
                    #                     client_demographics=client_demographics
                    #                 )
                    #             )

                    #             # Handle result/error
                    #             if isinstance(multilingual_result, dict) and multilingual_result.get("error"):
                    #                 st.error(f"Error evaluating multilingual needs: {multilingual_result['error']}")
                    #                 raise Exception(f"Multilingual needs analysis failed: {multilingual_result['error']}")
                    #             else:
                    #                 st.write("Multilingual Needs analysis successful.") # Debug message
                    #                 analysis_results['multilingual_needs'] = multilingual_result
                    #                 print(f"Debug - Multilingual Needs Result: {multilingual_result}")

                    #         except Exception as e:
                    #             st.error(f"Error during Multilingual Needs Analysis: {str(e)}")
                    #             error_occurred = True

                    # --- Step 4: Generate Final Report ---
                    if not error_occurred:
                         with st.spinner("Performing gap analysis (Step 4/4: Reporting)..."):
                            try:
                                st.write("Calling Generate Report tool...") # Debug message
                                
                                gap_report_agent = GapReportAssemblyAgent()
                                # Ensure all previous results are available
                                # if 'practice_gaps' in analysis_results and 'format_gaps' in analysis_results:# and 'multilingual_needs' in analysis_results:
                                    
                                gap_report_result_raw = gap_report_agent.process(f"""I have the following 
                                                                               analysis results that need to be compiled into a report:
                                                                               Practice Area Gaps:\n{analysis_results.get('practice_area_gaps')}\n
                                                                               Format Gaps:\n{analysis_results.get('format_gaps')}""")
                                

                                print(f'Debug:Gap Report Result Raw: {gap_report_result_raw}')
                                gap_report_result = gap_report_result_raw.content
                                print("HERERERERERER")
                                print(f'Debug:Gap Report Result: {gap_report_result}')



                                # Handle result/error
                                if isinstance(gap_report_result, dict) and gap_report_result.get("error"):
                                    st.error(f"Error generating final report: {gap_report_result['error']}")
                                    raise Exception(f"Report generation failed: {gap_report_result['error']}")
                                else:
                                    st.write("Final Report generation successful.") # Debug message
                                    # Store and display the final report
                                    # Assuming the report tool returns the markdown string directly or in a 'report'/'content' key
                                    # final_report_content = gap_report_result
                                    if isinstance(gap_report_result, dict):
                                        if 'report' in gap_report_result:
                                            final_report_content = gap_report_result['report']
                                        elif 'content' in gap_report_result:
                                            final_report_content = gap_report_result['content']
                                        # Add more potential keys if needed, or handle unexpected dict structure

                                    # Ensure content is a string before storing/displaying
                                    if not isinstance(gap_report_result, str):
                                        st.error("Generated report content is not in the expected format (string).")
                                        print(f"Debug - Unexpected report format: {type(gap_report_result)}")
                                        error_occurred = True
                                    else:
                                        st.session_state.gap_analysis = gap_report_result
                                        st.success("Gap analysis completed successfully!")
                                        st.markdown(st.session_state.gap_analysis) # Display the new report immediately
                                # else:
                                #      st.error("Missing results from previous analysis steps. Cannot generate final report.")
                                #      error_occurred = True

                            except Exception as e:
                                st.error(f"Error during Final Report Generation: {str(e)}")
                                error_occurred = True


        # Display previous gap analysis if available (This will now show the newly generated report)
        if st.session_state.gap_analysis:
            st.subheader("Previous Gap Analysis Results")
            st.markdown(st.session_state.gap_analysis)

            # Save button for previous analysis
            if st.button("Save This Gap Analysis"):
                try:
                    # Create outputs directory if it doesn't exist
                    os.makedirs("outputs", exist_ok=True)

                    # Save as markdown
                    with open("outputs/content_gap_analysis.md", "w") as f:
                        f.write(st.session_state.gap_analysis)

                    st.success("Gap analysis saved to outputs/content_gap_analysis.md")
                except Exception as e:
                    st.error(f"Error saving gap analysis: {str(e)}")
