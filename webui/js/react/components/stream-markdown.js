import React, { useEffect, useState } from "https://esm.sh/react@18.3.1";
import htm from "https://esm.sh/htm@3.1.1";

const html = htm.bind(React.createElement);

const STREAMDOWN_URL =
    "https://esm.sh/streamdown@latest?deps=react@18.3.1,react-dom@18.3.1";
let streamdownPromise = null;

async function loadStreamdownComponent() {
    if (streamdownPromise) {
        return streamdownPromise;
    }

    streamdownPromise = import(STREAMDOWN_URL)
        .then((mod) => mod.Streamdown || null)
        .catch((error) => {
            console.warn("Failed to load Streamdown:", error);
            return null;
        });

    return streamdownPromise;
}

export function StreamMarkdown({ content }) {
    const [StreamdownComponent, setStreamdownComponent] = useState(null);

    useEffect(() => {
        let mounted = true;

        loadStreamdownComponent().then((component) => {
            if (!mounted || !component) return;
            setStreamdownComponent(() => component);
        });

        return () => {
            mounted = false;
        };
    }, []);

    if (!StreamdownComponent) {
        return html`<div className="whitespace-pre-wrap">${content || ""}</div>`;
    }

    return html`
        <${StreamdownComponent} className="markdown-body text-sm leading-6" parseIncompleteMarkdown=${true}>
            ${String(content || "")}
        <//>
    `;
}
