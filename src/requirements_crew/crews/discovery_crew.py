from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew
from ..models.outputs import (
    SourceList,
    BriefAndRequirements,
    PersonaList,
    OpenQuestionList,
    RequirementList,
    DomainEntityList,
    MermaidDiagramList,
    QaReviewFindings,
    ProxyReviewFindings,
    UserStoryList,
)
from ..tools.llm import get_default_llm
from ..tools.serper import ScopedSerperTool

@CrewBase
class DiscoveryCrew:
    """Discovery and Requirements Gathering Crew."""
    
    agents_config = "../agents/agents.yaml"
    tasks_config = "../tasks/tasks.yaml"
    
    # ----------------------------------------------------
    # Agents
    # ----------------------------------------------------
    
    @agent
    def intake_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["intake_analyst"],
            llm=get_default_llm()
        )
        
    @agent
    def requirements_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["requirements_analyst"],
            llm=get_default_llm()
        )
        
    @agent
    def user_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["user_researcher"],
            llm=get_default_llm()
        )
        
    @agent
    def srs_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["srs_writer"],
            llm=get_default_llm()
        )
        
    @agent
    def domain_modeler(self) -> Agent:
        return Agent(
            config=self.agents_config["domain_modeler"],
            llm=get_default_llm()
        )
        
    @agent
    def uml_architect(self) -> Agent:
        return Agent(
            config=self.agents_config["uml_architect"],
            llm=get_default_llm()
        )
        
    @agent
    def requirements_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["requirements_reviewer"],
            llm=get_default_llm()
        )
        
    @agent
    def client_proxy(self) -> Agent:
        return Agent(
            config=self.agents_config["client_proxy"],
            llm=get_default_llm()
        )
        
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=get_default_llm(),
            tools=[ScopedSerperTool()]
        )

    @agent
    def user_story_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["user_story_writer"],
            llm=get_default_llm()
        )

    # ----------------------------------------------------
    # Tasks
    # ----------------------------------------------------
    
    @task
    def extract_statements(self) -> Task:
        return Task(
            config=self.tasks_config["extract_statements"],
            output_pydantic=SourceList
        )
        
    @task
    def draft_brief_and_requirements(self) -> Task:
        return Task(
            config=self.tasks_config["draft_brief_and_requirements"],
            context=[self.extract_statements()],
            output_pydantic=BriefAndRequirements
        )
        
    @task
    def build_personas(self) -> Task:
        return Task(
            config=self.tasks_config["build_personas"],
            output_pydantic=PersonaList
        )

    @task
    def generate_clarifying_questions(self) -> Task:
        return Task(
            config=self.tasks_config["generate_clarifying_questions"],
            output_pydantic=OpenQuestionList
        )

    @task
    def author_srs(self) -> Task:
        return Task(
            config=self.tasks_config["author_srs"],
            output_pydantic=RequirementList
        )

    @task
    def model_domain(self) -> Task:
        return Task(
            config=self.tasks_config["model_domain"],
            output_pydantic=DomainEntityList
        )

    @task
    def author_diagrams(self) -> Task:
        return Task(
            config=self.tasks_config["author_diagrams"],
            output_pydantic=MermaidDiagramList
        )

    @task
    def qa_review(self) -> Task:
        return Task(
            config=self.tasks_config["qa_review"],
            output_pydantic=QaReviewFindings
        )

    @task
    def proxy_review(self) -> Task:
        return Task(
            config=self.tasks_config["proxy_review"],
            output_pydantic=ProxyReviewFindings
        )

    @task
    def research_context(self) -> Task:
        return Task(
            config=self.tasks_config["research_context"],
            output_pydantic=OpenQuestionList
        )

    @task
    def author_user_stories(self) -> Task:
        return Task(
            config=self.tasks_config["author_user_stories"],
            output_pydantic=UserStoryList
        )

    # ----------------------------------------------------
    # Crew Orchestration
    # ----------------------------------------------------
    
    @crew
    def crew(self) -> Crew:
        # For M3, the Intake/Discovery crew runs only the first three sequential tasks:
        # extract_statements -> draft_brief_and_requirements -> build_personas
        return Crew(
            agents=[
                self.intake_analyst(),
                self.requirements_analyst(),
                self.user_researcher()
            ],
            tasks=[
                self.extract_statements(),
                self.draft_brief_and_requirements(),
                self.build_personas()
            ],
            process=Process.sequential,
            verbose=True
        )
