import React from "https://esm.sh/react@18.3.1";
import htm from "https://esm.sh/htm@3.1.1";

import { AssistantMessageArea } from "../pages/assistant-page.js";

const html = htm.bind(React.createElement);

export function AssistantMessageAreaMount({
    assistantCurrentSessionId,
    assistantSessions,
    assistantMessagesLoading,
    assistantComposedMessages,
    assistantError,
    assistantSkills,
    assistantSkillsLoading,
    assistantInput,
    setAssistantInput,
    assistantSending,
    handleSendAssistantMessage,
    assistantChatScrollRef,
}) {
    return html`
        <${AssistantMessageArea}
            assistantCurrentSessionId=${assistantCurrentSessionId}
            assistantSessions=${assistantSessions}
            assistantMessagesLoading=${assistantMessagesLoading}
            assistantComposedMessages=${assistantComposedMessages}
            assistantError=${assistantError}
            assistantSkills=${assistantSkills}
            assistantSkillsLoading=${assistantSkillsLoading}
            assistantInput=${assistantInput}
            setAssistantInput=${setAssistantInput}
            assistantSending=${assistantSending}
            onSendAssistantMessage=${handleSendAssistantMessage}
            assistantChatScrollRef=${assistantChatScrollRef}
        />
    `;
}
