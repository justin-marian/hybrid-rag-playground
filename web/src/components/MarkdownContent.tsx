import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";

interface MarkdownContentProps {
  text: string;
  className?: string;
  inline?: boolean;
}

export function normalizeMarkdown(text: string): string {
  return text
    // Convert literal "\n" into real newlines first.
    .replace(/\\\\n/g, "\n")
    .replace(/\\n/g, "\n")
    // Fix double-escaped markdown: \\*\\*Answer:\\*\\* -> **Answer:**
    .replace(/\\\\([`*_{}\[\]()#+\-.!>])/g, "$1")
    // Fix escaped markdown: \*\*Answer:\*\* -> **Answer:**
    .replace(/\\([`*_{}\[\]()#+\-.!>])/g, "$1")
    // Clean line endings/spaces.
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .trim();
}

function InlineParagraph({ children }: { children?: ReactNode }) {
  return <>{children}</>;
}

export function MarkdownContent({
  text,
  className = "",
  inline = false,
}: MarkdownContentProps) {
  const Wrapper = inline ? "span" : "div";
  const normalizedClassName = inline
    ? `markdown-body markdown-body--inline ${className}`.trim()
    : `markdown-body ${className}`.trim();

  return (
    <Wrapper className={normalizedClassName}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={inline ? { p: InlineParagraph } : undefined}
      >
        {normalizeMarkdown(text)}
      </ReactMarkdown>
    </Wrapper>
  );
}
