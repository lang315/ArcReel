import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { AssistantMessageArea } from "../src/react/pages/assistant-page.js";

function renderArea(extra = {}) {
    return renderToStaticMarkup(
        React.createElement(AssistantMessageArea, {
            assistantCurrentSessionId: "session-1",
            assistantSessions: [{ id: "session-1", title: "test 会话" }],
            assistantMessagesLoading: false,
            assistantComposedMessages: [],
            assistantError: "",
            assistantSkills: [],
            assistantSkillsLoading: false,
            assistantInput: "",
            setAssistantInput: () => {},
            assistantSending: false,
            assistantInterrupting: false,
            assistantAnsweringQuestion: false,
            sessionStatus: "idle",
            sessionStatusDetail: { status: "idle" },
            onSendAssistantMessage: () => {},
            onInterruptAssistantSession: () => {},
            onAnswerAssistantQuestion: () => {},
            assistantChatScrollRef: { current: null },
            assistantPendingQuestion: {
                id: "q-1",
                questions: [
                    {
                        header: "选择项目",
                        question: "问题A：选项目",
                        multiSelect: false,
                        options: [{ label: "test" }, { label: "创建新项目" }],
                    },
                    {
                        header: "视频内容",
                        question: "问题B：选内容",
                        multiSelect: false,
                        options: [{ label: "使用已有素材" }, { label: "我来描述内容" }],
                    },
                ],
            },
            ...extra,
        })
    );
}

test("pending question area should render wizard progress and only current question", () => {
    const markup = renderArea();

    assert.ok(markup.includes("问题 1/2"));
    assert.ok(markup.includes("下一题"));
    assert.ok(!markup.includes("提交答案"));
    assert.ok(markup.includes("问题A：选项目"));
    assert.ok(!markup.includes("问题B：选内容"));
});
