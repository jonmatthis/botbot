from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder, PromptTemplate,
)

from jonbot.backend.ai.chatbot.components.prompt.prompt_strings import (
    DEFAULT_RULES_FOR_LIVING,
    DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE, DEFAULT_MAIN_TASK, DEFAULT_FORMATTING_INSTRUCTIONS, DEFAULT_PERSONALITY,
)


class ChatbotPrompt(ChatPromptTemplate):
    @classmethod
    def build(
            cls,
            chat_history_placeholder_name: str,
            context_description_string: str,
            system_prompt_template: str = DEFAULT_CHATBOT_SYSTEM_PROMPT_TEMPLATE,
            config_prompts: str = None,
    ) -> ChatPromptTemplate:
        if config_prompts is None:
            config_prompts = ""

        if config_prompts != "":
            system_prompt = PromptTemplate(
                template=system_prompt_template,
                input_variables=[
                    "main_task",
                    "rules_for_living",
                    "personality",
                    "formatting",
                    "context_description",
                    "config_prompts",
                    # "vectorstore_memory"
                ],
            )
            partial_system_prompt = system_prompt.partial(
                main_task=DEFAULT_MAIN_TASK,
                rules_for_living=DEFAULT_RULES_FOR_LIVING,
                personality=DEFAULT_PERSONALITY,
                formatting=DEFAULT_FORMATTING_INSTRUCTIONS,
                context_description=context_description_string,
                config_prompts=config_prompts,

            )

            system_message_prompt = SystemMessagePromptTemplate(
                prompt=partial_system_prompt,
            )
        else:
            system_template = ""
            system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)

        human_template = "{human_input}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        return cls.from_messages(
            [
                system_message_prompt,
                MessagesPlaceholder(
                    variable_name=chat_history_placeholder_name,
                ),
                human_message_prompt,
            ]
        )


if __name__ == "__main__":
    print(ChatbotPrompt.build())
    f = 9
