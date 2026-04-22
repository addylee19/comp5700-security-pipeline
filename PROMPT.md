# PROMPT.md

## zero-shot

```text
You are a security requirements analyst.

Identify the key data elements (KDEs) in the security requirements document below.
A KDE can map to multiple requirements.

Return YAML only in this exact structure:
- element1:
    name: <kde name>
    requirements:
      - <requirement text>
      - <requirement text>
- element2:
    name: <kde name>
    requirements:
      - <requirement text>

Document:
<document_text>
```

## few-shot

```text
You are a security requirements analyst.

Extract key data elements (KDEs) and the requirements that mention them.
A KDE can map to more than one requirement.

Example:
Input snippet:
"Passwords must be rotated every 90 days. Password history must be preserved."

Example YAML output:
- element1:
    name: password
    requirements:
      - Passwords must be rotated every 90 days.
      - Password history must be preserved.

Now analyze the document below and return YAML only in the same structure.

Document:
<document_text>
```

## chain-of-thought

```text
You are a security requirements analyst.

Reason step by step to identify:
1. important security entities or data concepts,
2. which requirements mention each concept,
3. whether multiple requirements map to the same KDE.

Do the reasoning internally, but output ONLY final YAML in this exact structure:
- element1:
    name: <kde name>
    requirements:
      - <requirement text>
      - <requirement text>

Document:
<document_text>
```
