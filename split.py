import os
import re

source = '/Users/baydogan/Desktop/les/University/ISE307/Projects/Proje - 2/Project2_Revised.tex'
p2_out = '/Users/baydogan/Desktop/les/University/ISE307/Projects/Proje - 2/Project2.tex'
p3_dir = '/Users/baydogan/Desktop/les/University/ISE307/Projects/Proje - 3'
p3_out = os.path.join(p3_dir, 'Project3.tex')

if not os.path.exists(p3_dir):
    os.makedirs(p3_dir)

with open(source, 'r', encoding='utf-8') as f:
    text = f.read()

# Helper to find boundary lines
def get_lines(t):
    return t.split('\n')

lines = get_lines(text)

# 1. Prepare Preamble
preamble_end = text.find('\\begin{document}')
preamble = text[:preamble_end]

# Modify preamble to include shadows library
if 'shadows, shadows.blur' not in preamble:
    preamble = preamble.replace('decorations.pathreplacing}', 'decorations.pathreplacing, shadows, shadows.blur}')

# 2. Extract Phase 2 and Phase 3 contents based on \part markers
# Phase 2 starts after \tableofcontents \listoffigures \listoftables \newpage \section{Introduction} 
# Wait, actually Abstract, TOC, lists are in between. We need to skip Abstract, Intro, Glossary.

# Find \part{Systems Analysis (Phase 2)}
part2_idx = text.find('\\part{Systems Analysis (Phase 2)}')
if part2_idx == -1: part2_idx = text.find('\\part{Systems Analysis')

# Find \part{Systems Design (Phase 3)}
part3_idx = text.find('\\part{Systems Design (Phase 3)}')
if part3_idx == -1: part3_idx = text.find('\\part{Systems Design')

# Find Conclusion and Glossary
conclusion_idx = text.find('\\section{Conclusion}')
glossary_idx = text.find('\\section*{Glossary}')
end_doc_idx = text.find('\\end{document}')

phase2_content = text[part2_idx : part3_idx]
# Remove the \part{...} line itself since it's now the main title
phase2_content = re.sub(r'\\part\{Systems Analysis.*?\}\s*', '', phase2_content, flags=re.DOTALL)

phase3_content = text[part3_idx : glossary_idx]
phase3_content = re.sub(r'\\part\{Systems Design.*?\}\s*', '', phase3_content, flags=re.DOTALL)


# 3. Create Project 2
p2_preamble = preamble.replace('Project 2: Systems Analysis \& Design (SDLC Phases 2--3)', 'Project 2: Systems Analysis')
p2_preamble = p2_preamble.replace('System Analysis and Design -- ISE307 Project 2', 'Systems Analysis -- ISE307')
p2_preamble = p2_preamble.replace('S\\"{o}rg\\"{u}.ai System Analysis and Design', 'S\\"{o}rg\\"{u}.ai Systems Analysis')

p2_full = p2_preamble + """\\begin{document}
\\maketitle

\\tableofcontents
\\listoffigures
\\listoftables
\\newpage

""" + phase2_content.strip() + "\n\n\\end{document}\n"

# 4. Create Project 3
p3_preamble = preamble.replace('Project 2: Systems Analysis \& Design (SDLC Phases 2--3)', 'Project 3: Systems Design')
p3_preamble = p3_preamble.replace('System Analysis and Design -- ISE307 Project 2', 'Systems Design -- ISE307 Project 3')
p3_preamble = p3_preamble.replace('S\\"{o}rg\\"{u}.ai System Analysis and Design', 'S\\"{o}rg\\"{u}.ai Systems Design')
p3_preamble = p3_preamble.replace('ISE 307 -- Project 2:', 'ISE 307 -- Project 3:')

p3_full = p3_preamble + """\\begin{document}
\\maketitle

\\tableofcontents
\\listoffigures
\\listoftables
\\newpage

""" + phase3_content.strip() + "\n\n\\end{document}\n"

# 5. TikZ Aesthetics Refinements
# I will use regular expressions and manual replacements to carefully update the tikz styles in p2 and p3.
# This ensures alignment issues are fixed while preserving context verbatim!

# Diagram 1: Use Case Diagram
new_usecase = r'''\begin{tikzpicture}[node distance=2cm and 2.5cm, font=\footnotesize, >=Stealth,
    actor/.style={align=center, font=\bfseries},
    usecase/.style={ellipse, draw, fill=blue!10, minimum width=3cm, align=center, drop shadow={opacity=0.2}},
    system/.style={thick, fill=gray!5, rounded corners, drop shadow={opacity=0.1}}]
    
    % Actors
    \node[actor] (emp) {\textbf{Employee}};
    \node[actor, below=3cm of emp] (mgr) {\textbf{HR Manager}};
    
    % Usecases
    \node[usecase, right=3.5cm of emp] (uc1) {Query HR\\Policies (AI)};
    \node[usecase, above=1cm of uc1] (uc_auth) {Authenticate\\User};
    \node[usecase, fill=red!10, dashed, below=1cm of uc1] (uc_esc) {Escalate to\\Human};
    \node[usecase, below=1cm of uc_esc] (uc2) {Submit Workflow\\Request};
    \node[usecase, below=1cm of uc2] (uc3) {Manage \& Approve\\Requests};
    \node[usecase, below=1cm of uc3] (uc4) {Ingest Knowledge\\Base};

    % External Actors Right
    \node[actor, right=3.5cm of uc_auth] (admin) {\textbf{HR Admin}};
    \node[actor, right=3.5cm of uc3] (hris) {\textbf{External HRIS}};

    % System Boundary - fit around usecases
    \begin{scope}[on background layer]
        \node[system, fit=(uc_auth) (uc1) (uc_esc) (uc2) (uc3) (uc4), inner sep=1cm] (boundary) {};
        \node[font=\bfseries, text=black!70, anchor=south] at (boundary.north) {S\"{o}rg\"{u}.ai System Boundary};
    \end{scope}

    % Actor to Use Case Connections
    \draw (emp) -- (uc1);
    \draw (emp) -- (uc2);
    \draw (mgr) -- (uc1);
    \draw (mgr) -- (uc2);
    \draw (mgr) -- (uc3);
    \draw (admin) -- (uc4);
    \draw (hris) -- (uc3);
    \draw (hris) -- (uc4);

    % Includes and Extends
    \draw[->, dashed] (uc1) -- node[right, font=\tiny] {<<include>>} (uc_auth);
    \draw[->, dashed] (uc2) edge[bend right=30] node[right, font=\tiny] {<<include>>} (uc_auth);
    \draw[->, dashed] (uc_esc) -- node[right, font=\tiny] {<<extend>>} (uc1);
\end{tikzpicture}'''

p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=2\.5cm, font=\\footnotesize\].*?\\end\{tikzpicture\}', new_usecase.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# Diagram 2: Context Diagram
new_context = r'''\begin{tikzpicture}[node distance=4cm and 5cm, font=\small, >=Stealth,
    entity/.style={rectangle, draw, fill=blue!10, minimum width=2.5cm, minimum height=1.5cm, drop shadow={opacity=0.2}},
    process/.style={circle, draw, fill=green!10, minimum size=3.5cm, drop shadow={opacity=0.2}}]

    \node[process] (system) {\textbf{S\"{o}rg\"{u}.ai}\\(0.0)};
    \node[entity, above left=1cm and 2cm of system] (employee) {Employee};
    \node[entity, above right=1cm and 2cm of system] (hr_manager) {HR Manager};
    \node[entity, below left=1cm and 2cm of system] (hr_admin) {HR Admin};
    \node[entity, below right=1cm and 2cm of system] (hris) {External HRIS};

    \draw[->, thick] (employee) edge[bend left=15] node[midway, above, font=\scriptsize, sloped] {HR Query / Workflow Req.} (system);
    \draw[->, thick] (system) edge[bend left=15] node[midway, below, font=\scriptsize, sloped] {AI Answer / Status Update} (employee);
    
    \draw[->, thick] (hr_manager) edge[bend left=15] node[midway, above, font=\scriptsize, sloped] {Approvals / Esc. Replies} (system);
    \draw[->, thick] (system) edge[bend left=15] node[midway, below, font=\scriptsize, sloped] {Pending Approvals} (hr_manager);
    
    \draw[->, thick] (hr_admin) edge[bend left=15] node[midway, below, font=\scriptsize, sloped] {Policy Docs / Config} (system);
    \draw[->, thick] (system) edge[bend left=15] node[midway, above, font=\scriptsize, sloped] {Analytics / Logs} (hr_admin);
    
    \draw[->, thick] (hris) edge[bend left=15] node[midway, below, font=\scriptsize, sloped] {Employee \& Org Data} (system);
    \draw[->, thick] (system) edge[bend left=15] node[midway, above, font=\scriptsize, sloped] {Approved Workflow Sync} (hris);
\end{tikzpicture}'''

p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=3\.5cm, font=\\small\].*?\\end\{tikzpicture\}', new_context.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# Diagram 3: Level 1 DFD
new_l1 = r'''\begin{tikzpicture}[node distance=2.5cm and 3cm, font=\scriptsize, >=Stealth,
    entity/.style={rectangle, draw, fill=blue!10, minimum width=2.5cm, drop shadow={opacity=0.2}},
    process/.style={ellipse, draw, fill=green!10, text width=2.5cm, align=center, drop shadow={opacity=0.2}},
    store/.style={rectangle, draw, fill=yellow!10, minimum width=3cm, drop shadow={opacity=0.2}}]

    % Processes
    \node[process] (p2) {2.0\\Process AI\\Inquiry (RAG)};
    \node[process, above=2cm of p2] (p1) {1.0\\Ingest \& Embed\\Documents};
    \node[process, below=2cm of p2] (p3) {3.0\\Manage HR\\Workflows};

    % Entities
    \node[entity, left=3cm of p1] (ext_admin) {HR Admin};
    \node[entity, left=3cm of p2] (ext_emp) {Employee};
    \node[entity, left=3cm of p3] (ext_mgr) {HR Manager};

    % Data Stores
    \node[store, right=3cm of p1] (d1) {D1: Vector KB};
    \node[store, right=3cm of p2] (d2) {D2: Interaction Log};
    \node[store, right=3cm of p3] (d3) {D3: Request DB};

    % Flows
    \draw[->] (ext_admin) -- node[above] {Upload Policies} (p1);
    \draw[->] (p1) -- node[above] {Embeddings/Chunks} (d1);
    
    \draw[->] (ext_emp) -- node[above] {HR Question} (p2);
    \draw[->] (d1) edge[bend left=20] node[right] {Context Snippets} (p2);
    \draw[->] (p2) edge[bend left=20] node[left] {Semantic Query} (d1);
    \draw[->] (p2) edge[bend left=15] node[below] {AI Response} (ext_emp);
    \draw[->] (p2) -- node[above] {Log Interaction} (d2);
    
    \draw[->] (ext_emp) edge[bend right=20] node[left] {Submit Request} (p3);
    \draw[->] (p3) -- node[above] {Store Req} (d3);
    \draw[->] (p3) -- node[above] {Notify} (ext_mgr);
    \draw[->] (ext_mgr) edge[bend right=20] node[right] {Approve/Reject} (p3);
\end{tikzpicture}'''

# Note: The Level 1 DFD in original code looks like: \begin{tikzpicture}[node distance=2.5cm, font=\scriptsize] % Entities \node[rectangle, draw, fill=blue...
p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=2\.5cm, font=\\scriptsize\].*?\% Entities.*?\\end\{tikzpicture\}', new_l1.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# Diagram 4: Level 2 DFD (AI Inquiry)
# Need to distinguish finding for the L2 DFDs since they start similarly.
new_l2_ai = r'''\begin{tikzpicture}[node distance=2cm and 2.5cm, font=\scriptsize, >=Stealth,
    entity/.style={rectangle, draw, fill=blue!10, minimum width=2.5cm, drop shadow={opacity=0.2}},
    process/.style={ellipse, draw, fill=green!10, text width=2cm, align=center, drop shadow={opacity=0.2}},
    store/.style={rectangle, draw, fill=yellow!10, minimum width=2.5cm, drop shadow={opacity=0.2}}]

    \node[entity] (emp) {Employee};
    \node[process, right=2cm of emp] (p21) {2.1\\Parse \& Sanitize\\Query};
    \node[process, above right=1cm and 1cm of p21] (p22) {2.2\\Generate\\Embeddings};
    \node[process, right=2cm of p22] (p23) {2.3\\Execute Semantic\\Search};
    \node[store, above=1.5cm of p23] (d1) {D1: Vector KB};
    \node[process, right=2cm of p21] (p24) {2.4\\Synthesize LLM\\Response};
    \node[process, below right=1cm and 1cm of p24] (p25) {2.5\\Evaluate\\Confidence};
    \node[store, right=2cm of p25] (d2) {D2: Escalation DB};
    \node[entity, below=1.5cm of d2] (mgr) {HR Manager};

    \draw[->] (emp) -- node[above] {Raw Query} (p21);
    \draw[->] (p21) -- node[left] {Cleaned} (p22);
    \draw[->] (p22) -- node[above] {Vector} (p23);
    \draw[->] (p23) -- node[left] {Query} (d1);
    \draw[->] (d1) edge[bend left=15] node[right] {Top-K} (p23);
    \draw[->] (p23) -- node[right] {Payload} (p24);
    \draw[->] (p21) edge[bend right=20] node[below] {Original} (p24);
    \draw[->] (p24) -- node[right] {Draft + Score} (p25);
    \draw[->] (p25) edge[bend left=20] node[above] {Score $\ge$ 80\%} (emp);
    \draw[->] (p25) -- node[above] {Score < 80\%} (d2);
    \draw[->] (d2) -- node[right] {Alert} (mgr);
\end{tikzpicture}'''
p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=2cm, font=\\scriptsize\].*?\{Employee\}.*?HR Manager.*?\\end\{tikzpicture\}', new_l2_ai.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# State Transition Diagram
new_state = r'''\begin{tikzpicture}[node distance=3.5cm, font=\small, >=Stealth,
    state/.style={rectangle, rounded corners=5pt, draw, minimum width=2.5cm, minimum height=0.8cm, align=center, drop shadow={opacity=0.2}}]

    \node[state, fill=blue!15] (created) {Created};
    \node[state, fill=yellow!15, right of=created] (review) {Under Review};
    \node[state, fill=green!15, above right=1cm and 2.5cm of review] (approved) {Approved};
    \node[state, fill=red!15, below right=1cm and 2.5cm of review] (rejected) {Rejected};
    \node[state, fill=green!25, right of=approved] (completed) {Completed};
    \node[state, fill=gray!20, right of=rejected] (closed) {Closed};

    \draw[->, thick] (created) -- node[above, font=\scriptsize] {Submit} (review);
    \draw[->, thick] (review) -- node[above, sloped, font=\scriptsize] {Approve} (approved);
    \draw[->, thick] (review) -- node[below, sloped, font=\scriptsize] {Reject} (rejected);
    \draw[->, thick] (approved) -- node[above, font=\scriptsize] {Execute} (completed);
    \draw[->, thick] (rejected) -- node[above, font=\scriptsize] {Archive} (closed);
    \draw[->, thick, dashed] (review) edge[loop above] node[above, font=\scriptsize] {Escalate} (review);
\end{tikzpicture}'''
p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=3cm, font=\\small,\s*state/\.style=.*?\\end\{tikzpicture\}', new_state.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# ER Diagram
new_er = r'''\begin{tikzpicture}[node distance=2cm and 2.5cm, font=\scriptsize, >=Stealth, 
    every node/.style={draw, rectangle, minimum width=3cm, minimum height=1cm, align=left, fill=gray!5, drop shadow={opacity=0.15}}]

    \node (company) {\textbf{COMPANY} \\ \underline{CompID} (PK) \\ Name \\ PlanType \\ GDPR\_Consent};
    \node[below left=2cm and 1cm of company] (user) {\textbf{USER} \\ \underline{UserID} (PK) \\ CompID (FK) \\ Name \\ Email \\ Role (RBAC)};
    \node[below right=2cm and 1cm of company] (doc) {\textbf{DOCUMENT} \\ \underline{DocID} (PK) \\ CompID (FK) \\ Title \\ UploadDate \\ Status};
    \node[below=2cm of doc] (policy) {\textbf{POLICY\_CHUNK} \\ \underline{ChunkID} (PK) \\ DocID (FK) \\ ContentText \\ VectorEmbedding};
    \node[below=2cm of user] (request) {\textbf{HR\_REQUEST} \\ \underline{ReqID} (PK) \\ UserID (FK) \\ ReqType \\ Status};
    \node[right=2.5cm of request] (action) {\textbf{REQ\_ACTION} \\ \underline{ActionID} (PK) \\ ReqID (FK) \\ ActorID (FK) \\ Decision};
    \node[above=2cm of action] (intlog) {\textbf{INTERACTION\_LOG} \\ \underline{LogID} (PK) \\ UserID (FK) \\ CompID (FK) \\ QueryText \\ Confidence};

    \draw[thick, <->] (company) -- node[above, font=\tiny, sloped, draw=none, fill=none] {1:N (Has)} (user);
    \draw[thick, <->] (company) -- node[above, font=\tiny, sloped, draw=none, fill=none] {1:N (Owns)} (doc);
    \draw[thick, <->] (doc) -- node[right, font=\tiny, draw=none, fill=none] {1:N (Contains)} (policy);
    \draw[thick, <->] (user) -- node[right, font=\tiny, draw=none, fill=none] {1:N (Initiates)} (request);
    \draw[thick, <->] (request) -- node[above, font=\tiny, draw=none, fill=none] {1:N (Logged In)} (action);
    \draw[thick, <->] (user) edge[bend left=15] node[above, font=\tiny, sloped, draw=none, fill=none] {1:N (Performs)} (action);
    \draw[thick, <->] (user) -- node[above, font=\tiny, draw=none, fill=none] {1:N (Generates)} (intlog);
\end{tikzpicture}'''
p2_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=2\.5cm, font=\\scriptsize, every node/.style=.*?\\end\{tikzpicture\}', new_er.replace('\\', '\\\\'), p2_full, flags=re.DOTALL)


# Architecture Diagram in P3
new_arch = r'''\begin{tikzpicture}[node distance=1.5cm, font=\scriptsize, >=Stealth,
    layer/.style={rectangle, draw, rounded corners=3pt, minimum height=0.8cm, align=center, fill opacity=0.9},
    service/.style={rectangle, draw, fill=green!10, rounded corners=3pt, minimum width=2.2cm, minimum height=0.8cm, align=center, drop shadow={opacity=0.2}},
    store/.style={rectangle, draw, fill=yellow!10, rounded corners=3pt, minimum width=2cm, minimum height=0.8cm, align=center, drop shadow={opacity=0.2}}]

    % Presentation Layer
    \node[layer, fill=blue!10, minimum width=12cm] (pres) at (6, 10) {\textbf{Presentation Layer}};
    \node[service, fill=blue!15] (web) at (3, 9.4) {React SPA\\(Web App)};
    \node[service, fill=blue!15] (mobile) at (6, 9.4) {React Native\\(Mobile App)};
    \node[service, fill=blue!15] (hrisapi) at (9, 9.4) {HRIS REST API\\(Integration)};

    % API Gateway
    \node[layer, fill=purple!10, minimum width=12cm] (gw) at (6, 7.5) {\textbf{API Gateway Layer} (Nginx / Kong)\\[2mm]{\tiny \color{purple!70!black} Rate Limiting $\cdot$ JWT Validation $\cdot$ Load Balancing}};

    % Application Layer
    \node[layer, fill=green!5, minimum width=12cm] (app) at (6, 5) {\textbf{Application Layer} (FastAPI Microservices)};
    \node[service] (auth) at (1.5, 4.4) {Auth\\Service};
    \node[service] (rag) at (4.5, 4.4) {RAG\\Engine};
    \node[service] (wf) at (7.5, 4.4) {Workflow\\Engine};
    \node[service] (adm) at (10.5, 4.4) {Admin\\Service};

    % Data Layer
    \node[layer, fill=yellow!5, minimum width=12cm] (data) at (6, 2) {\textbf{Data Layer}};
    \node[store] (pg) at (1.5, 1.4) {PostgreSQL\\+ pgvector};
    \node[store] (redis) at (4.5, 1.4) {Redis\\(Cache)};
    \node[store] (minio) at (7.5, 1.4) {MinIO\\(Object Store)};
    \node[store] (llmext) at (10.5, 1.4) {LLM API\\(External)};

    % Connections (Orthogonal Routing)
    \draw[->, thick, rounded corners] (web.south) -- +(0,-0.5) -| (gw.north);
    \draw[->, thick, rounded corners] (mobile.south) -- (gw.north);
    \draw[->, thick, rounded corners] (hrisapi.south) -- +(0,-0.5) -| (gw.north);
    
    \draw[->, thick] (gw.south) -- (app.north);
    
    \draw[->, thick, rounded corners] (auth.south) -- (pg.north);
    \draw[->, thick, rounded corners] (rag.south) -- +(0,-0.5) -| (pg.north);
    \draw[->, thick, rounded corners] (rag.south) -- (redis.north);
    \draw[->, thick, rounded corners] (rag.south) -- +(0,-0.5) -| (llmext.north);
    \draw[->, thick, rounded corners] (wf.south) -- +(0,-0.5) -| (pg.north);
    \draw[->, thick, rounded corners] (adm.south) -- +(0,-0.5) -| (pg.north);
    \draw[->, thick, rounded corners] (adm.south) -- +(0,-0.5) -| (minio.north);
\end{tikzpicture}'''
p3_full = re.sub(r'\\begin\{tikzpicture\}\[node distance=1\.5cm, font=\\scriptsize,.*?\\end\{tikzpicture\}', new_arch.replace('\\', '\\\\'), p3_full, flags=re.DOTALL)


# Program Structure Chart in P3
new_struct = r'''\begin{tikzpicture}[node distance=1.5cm and 0.5cm, font=\scriptsize, >=Stealth,
    mod/.style={rectangle, draw, fill=gray!10, rounded corners=2pt, minimum width=2.2cm, minimum height=0.7cm, align=center, drop shadow={opacity=0.2}},
    sub/.style={rectangle, draw, fill=white, rounded corners=2pt, minimum width=1.8cm, minimum height=0.6cm, align=center, drop shadow={opacity=0.1}}]

    % Root
    \node[mod, fill=blue!15, minimum width=3cm] (root) {\textbf{S\"{o}rg\"{u}.ai}\\Main System};

    % Level 1 Modules
    \node[mod, fill=green!10, below left=1.5cm and 2.5cm of root] (ai) {AI Query\\Module};
    \node[mod, fill=green!10, left=1cm of ai] (auth) {Authentication\\Module};
    \node[mod, fill=green!10, below right=1.5cm and 2.5cm of root] (wf) {Workflow\\Module};
    \node[mod, fill=green!10, right=1cm of wf] (adm) {Administration\\Module};

    % Auth children
    \node[sub, below=1cm of auth] (a2) {Token\\Manager};
    \node[sub, left=0.2cm of a2] (a1) {Login/Logout\\Handler};
    \node[sub, right=0.2cm of a2] (a3) {RBAC\\Validator};

    % AI children
    \node[sub, below=1cm of ai] (q2) {Semantic\\Search};
    \node[sub, left=0.2cm of q2] (q1) {Query\\Parser};
    \node[sub, right=0.2cm of q2] (q3) {LLM\\Synthesizer};

    % Workflow children
    \node[sub, below=1cm of wf] (w2) {Approval\\Processor};
    \node[sub, left=0.2cm of w2] (w1) {Request\\Handler};
    \node[sub, right=0.2cm of w2] (w3) {Notification\\Dispatcher};

    % Admin children
    \node[sub, below=1cm of adm] (d2) {User\\Manager};
    \node[sub, left=0.2cm of d2] (d1) {Document\\Ingestor};
    \node[sub, right=0.2cm of d2] (d3) {Analytics\\Engine};

    % Edges with orthogonal routing
    \draw[-, thick] (root.south) -- +(0,-0.5) -| (auth.north);
    \draw[-, thick] (root.south) -- +(0,-0.5) -| (ai.north);
    \draw[-, thick] (root.south) -- +(0,-0.5) -| (wf.north);
    \draw[-, thick] (root.south) -- +(0,-0.5) -| (adm.north);
    
    \draw[-, thick] (auth.south) -- +(0,-0.3) -| (a1.north);
    \draw[-, thick] (auth.south) -- (a2.north);
    \draw[-, thick] (auth.south) -- +(0,-0.3) -| (a3.north);
    
    \draw[-, thick] (ai.south) -- +(0,-0.3) -| (q1.north);
    \draw[-, thick] (ai.south) -- (q2.north);
    \draw[-, thick] (ai.south) -- +(0,-0.3) -| (q3.north);
    
    \draw[-, thick] (wf.south) -- +(0,-0.3) -| (w1.north);
    \draw[-, thick] (wf.south) -- (w2.north);
    \draw[-, thick] (wf.south) -- +(0,-0.3) -| (w3.north);
    
    \draw[-, thick] (adm.south) -- +(0,-0.3) -| (d1.north);
    \draw[-, thick] (adm.south) -- (d2.north);
    \draw[-, thick] (adm.south) -- +(0,-0.3) -| (d3.north);
\end{tikzpicture}'''
p3_full = re.sub(r'\\begin\{tikzpicture\}\[font=\\scriptsize,\\s*mod/\.style=.*?\\end\{tikzpicture\}', new_struct.replace('\\', '\\\\'), p3_full, flags=re.DOTALL)


# Apply shadows to UI prototypes in P3 to make them look more polished
p3_full = p3_full.replace(r'\draw[thick, rounded corners=5pt] (0,0) rectangle (10,13);', r'\draw[thick, rounded corners=5pt, drop shadow={opacity=0.1}] (0,0) rectangle (10,13);')
p3_full = p3_full.replace(r'\draw[thick, rounded corners=5pt] (0,0) rectangle (14,10);', r'\draw[thick, rounded corners=5pt, drop shadow={opacity=0.1}] (0,0) rectangle (14,10);')


with open(p2_out, 'w', encoding='utf-8') as f:
    f.write(p2_full)

with open(p3_out, 'w', encoding='utf-8') as f:
    f.write(p3_full)

print("Split and refine completed successfully.")
