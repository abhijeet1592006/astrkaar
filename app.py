from flask import Flask, render_template_string, request, session, redirect, url_for, flash, abort
from datetime import datetime
import sqlite3
import uuid
import random
import time 
import threading
import time
import urllib.request

app = Flask(__name__)
app.secret_key = 'astrkaar_classified_directive_sigma_99'
import os
# If hosted on Vercel, use the /tmp directory to avoid read-only crashes
if os.environ.get('VERCEL'):
    DB_FILE = '/tmp/astrkaar.db'
else:
    DB_FILE = 'astrkaar.db'

# --- DATABASE SETUP (SQLite3) ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, password TEXT, role TEXT, name TEXT, clearance TEXT, ts_access INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, title TEXT, desc TEXT, status TEXT, lead TEXT, ts_access INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, sender TEXT, receiver TEXT, content TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, assigned_by TEXT, assigned_to TEXT, description TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, user TEXT, date TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contributions (id TEXT PRIMARY KEY, project_id TEXT, user TEXT, date TEXT, content TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES ('admin', 'admin', 'admin', 'System Administrator', 'OMEGA', 1)")
        c.execute("INSERT INTO users VALUES ('ceo', 'ceo', 'ceo', 'Chief Executive Officer', 'LEVEL 5', 1)")
        c.execute("INSERT INTO users VALUES ('founder', 'founder', 'cofounder', 'Co-Founder', 'LEVEL 5', 1)")
    
    conn.commit()
    conn.close()

init_db()

# --- HTML TEMPLATES ---

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASTRKAAR | SECURE MAINFRAME</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg-dark: #050505; --panel: #111111; --border: #333333; --accent-cyan: #00e5ff; --accent-green: #00ff41; --accent-red: #ff003c; }
        body { background-color: var(--bg-dark); color: #d4d4d4; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        .mono { font-family: 'Share Tech Mono', monospace; }
        .scanlines { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03)); background-size: 100% 3px, 3px 100%; pointer-events: none; z-index: 9999; opacity: 0.6;}
        .cyber-border { border: 1px solid var(--border); position: relative; background: var(--panel); }
        .cyber-border::before { content: ''; position: absolute; top: -1px; left: -1px; width: 10px; height: 10px; border-top: 2px solid var(--accent-cyan); border-left: 2px solid var(--accent-cyan); }
        .cyber-border::after { content: ''; position: absolute; bottom: -1px; right: -1px; width: 10px; height: 10px; border-bottom: 2px solid var(--accent-cyan); border-right: 2px solid var(--accent-cyan); }
        .ts-border { border-color: var(--accent-red) !important; background: rgba(255,0,60,0.05); }
        .ts-border::before, .ts-border::after { border-color: var(--accent-red) !important; }
        .glow-text { text-shadow: 0 0 5px rgba(0, 229, 255, 0.5); }
        .glow-red { text-shadow: 0 0 5px rgba(255, 0, 60, 0.7); }
        .input-cyber { background: #0a0a0a; border: 1px solid #333; color: var(--accent-cyan); font-family: 'Share Tech Mono'; transition: border 0.3s; }
        .input-cyber:focus { outline: none; border-color: var(--accent-cyan); box-shadow: 0 0 8px rgba(0,229,255,0.2); }
        .btn-cyber { background: transparent; border: 1px solid var(--accent-cyan); color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 2px; transition: all 0.3s; cursor: pointer; }
        .btn-cyber:hover { background: var(--accent-cyan); color: #000; box-shadow: 0 0 15px rgba(0,229,255,0.4); }
        .btn-red { border: 1px solid var(--accent-red); color: var(--accent-red); }
        .btn-red:hover { background: var(--accent-red); color: #fff; box-shadow: 0 0 15px rgba(255,0,60,0.4); }
        .bg-grid { background-image: linear-gradient(#111 1px, transparent 1px), linear-gradient(90deg, #111 1px, transparent 1px); background-size: 30px 30px; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #050505; }
        ::-webkit-scrollbar-thumb { background: #333; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
    </style>
</head>
<body class="bg-grid antialiased h-screen flex flex-col">
    <div class="scanlines"></div>
    [[CONTENT_PLACEHOLDER]]
</body>
</html>
"""

LOGIN_HTML = """
<div class="flex-1 flex items-center justify-center p-4">
    <div class="cyber-border w-full max-w-md p-8 relative z-10 shadow-2xl shadow-black">
        <div class="text-center mb-8">
            <h1 class="mono text-4xl text-cyan-400 glow-text tracking-widest font-bold">ASTRKAAR</h1>
            <p class="mono text-xs text-red-500 mt-2 glow-red uppercase">Classified Deep Tech Facility</p>
            <p class="mono text-xs text-zinc-500 mt-1 uppercase">Authorized Personnel Only</p>
        </div>
        
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="mb-4 p-2 border border-red-500 bg-red-900/20 text-red-400 mono text-xs text-center">
              {{ messages[0] }}
            </div>
          {% endif %}
        {% endwith %}

        <form action="/login" method="POST" class="space-y-6">
            <div>
                <label class="mono text-xs text-zinc-400 uppercase tracking-wider block mb-2">Identification Link</label>
                <input type="text" name="username" class="input-cyber w-full p-3 text-sm" required autocomplete="off" placeholder="Enter ID...">
            </div>
            <div>
                <label class="mono text-xs text-zinc-400 uppercase tracking-wider block mb-2">Security Passcode</label>
                <input type="password" name="password" class="input-cyber w-full p-3 text-sm" required placeholder="••••••••">
            </div>
            <button type="submit" class="btn-cyber w-full py-3 mono text-sm font-bold mt-4">Initiate Handshake</button>
        </form>
    </div>
</div>
"""

DASHBOARD_HTML = """
<div class="flex h-screen overflow-hidden relative z-10">
    <aside class="w-64 border-r border-zinc-800 bg-[#0a0a0a] flex flex-col z-20">
        <div class="p-6 border-b border-zinc-800 text-center">
            <h2 class="mono text-2xl text-cyan-400 glow-text font-bold tracking-widest">ASTRKAAR</h2>
            <div class="mt-4 flex flex-col items-center">
                <div class="w-16 h-16 rounded-full border-2 border-cyan-400 flex items-center justify-center mb-2 shadow-[0_0_10px_rgba(0,229,255,0.3)] bg-zinc-900">
                    <span class="mono text-xl text-cyan-400">{{ user.name[0] }}</span>
                </div>
                <span class="mono text-sm text-zinc-300">{{ user.name }}</span>
                <span class="mono text-[10px] text-red-500 border border-red-500 px-2 py-0.5 mt-1 rounded uppercase">CLR: {{ user.clearance }}</span>
                {% if user.ts_access %}
                <span class="mono text-[10px] bg-red-900 text-white px-2 py-0.5 mt-1 rounded uppercase glow-red font-bold">TS-ACTIVE</span>
                {% endif %}
            </div>
        </div>
        
        <nav class="flex-1 p-4 space-y-2 mono text-sm overflow-y-auto">
            <button onclick="switchTab('projects')" class="nav-btn w-full text-left p-3 hover:bg-zinc-900 border-l-2 border-transparent hover:border-cyan-400 text-zinc-400 hover:text-cyan-400 transition-colors" id="nav-projects">[01] PROJECTS DATABANK</button>
            <button onclick="switchTab('comms')" class="nav-btn w-full text-left p-3 hover:bg-zinc-900 border-l-2 border-transparent hover:border-cyan-400 text-zinc-400 hover:text-cyan-400 transition-colors" id="nav-comms">[02] SECURE COMMS</button>
            <button onclick="switchTab('tasks')" class="nav-btn w-full text-left p-3 hover:bg-zinc-900 border-l-2 border-transparent hover:border-cyan-400 text-zinc-400 hover:text-cyan-400 transition-colors" id="nav-tasks">[03] DIRECTIVES & TASKS</button>
            <button onclick="switchTab('reports')" class="nav-btn w-full text-left p-3 hover:bg-zinc-900 border-l-2 border-transparent hover:border-cyan-400 text-zinc-400 hover:text-cyan-400 transition-colors" id="nav-reports">[04] DAILY REPORT LOG</button>
            
            {% if user.role == 'admin' %}
            <div class="pt-4 mt-4 border-t border-zinc-800">
                <button onclick="switchTab('admin')" class="nav-btn w-full text-left p-3 bg-red-950/20 hover:bg-red-900/40 border-l-2 border-red-500 text-red-400 transition-colors" id="nav-admin">[XX] ADMIN TERMINAL</button>
            </div>
            {% endif %}
        </nav>
        
        <div class="p-4 border-t border-zinc-800">
            <a href="/logout" class="block text-center w-full p-2 border border-zinc-700 text-zinc-500 hover:text-red-400 hover:border-red-500 mono text-xs transition-colors">TERMINATE SESSION</a>
        </div>
    </aside>

    <main class="flex-1 bg-[#050505] p-8 overflow-y-auto relative z-10">
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="mb-6 p-3 border border-[#00ff41] bg-[#00ff41]/10 text-[#00ff41] mono text-sm shadow-[0_0_10px_rgba(0,255,65,0.2)]">
              SYS_MSG: {{ messages[0] }}
            </div>
          {% endif %}
        {% endwith %}

        <section id="tab-projects" class="tab-content hidden">
            <h2 class="mono text-2xl text-cyan-400 mb-6 border-b border-zinc-800 pb-2 tracking-widest uppercase">ACTIVE PROJECTS DATABANK</h2>
            
            {% if user.role in ['ceo', 'cofounder', 'admin'] %}
            <div class="cyber-border p-6 mb-8 bg-[#0a0a0a]">
                <h3 class="mono text-cyan-400 mb-4 uppercase font-bold text-sm">INITIATE NEW PROJECT DIRECTIVE</h3>
                <form action="/create_project" method="POST" class="flex flex-col gap-4">
                    <div class="flex flex-col lg:flex-row gap-4">
                        <input type="text" name="title" class="input-cyber p-2 text-sm lg:w-1/4" placeholder="Project Codename..." required>
                        <input type="text" name="desc" class="input-cyber p-2 text-sm flex-1" placeholder="Objective parameters..." required>
                        <select name="status" class="input-cyber p-2 text-sm lg:w-1/6" required>
                            <option value="Active">Active</option>
                            <option value="Classified">Classified</option>
                            <option value="Archived">Archived</option>
                        </select>
                        <button type="submit" class="btn-cyber py-2 px-6 mono text-sm font-bold">INITIALIZE</button>
                    </div>
                    <label class="flex items-center space-x-2 w-max cursor-pointer border border-zinc-800 p-2 hover:bg-zinc-900">
                        <input type="checkbox" name="ts_access" value="1" class="w-4 h-4 accent-red-600 bg-black">
                        <span class="mono text-xs text-red-500 font-bold uppercase glow-red">Classify as Top Secret / Restricted</span>
                    </label>
                </form>
            </div>
            {% endif %}

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {% for prj in db.projects %}
                <div class="cyber-border p-6 hover:shadow-[0_0_15px_rgba(0,229,255,0.1)] transition-shadow {% if prj.ts_access %} ts-border {% endif %} flex flex-col justify-between">
                    <div>
                        {% if prj.ts_access %}
                        <div class="mb-3">
                            <span class="mono text-[10px] text-red-500 font-bold border border-red-500 px-2 py-0.5 bg-red-900/20 uppercase glow-red">⚠ TOP SECRET FILE ⚠</span>
                        </div>
                        {% endif %}
                        <div class="flex justify-between items-start mb-4">
                            <h3 class="text-xl font-semibold text-zinc-200">{{ prj.title }}</h3>
                            <span class="mono text-xs px-2 py-1 bg-zinc-900 border {{ 'border-red-500 text-red-500' if prj.status == 'Classified' else 'border-[#00ff41] text-[#00ff41]' }}">{{ prj.id }} | {{ prj.status }}</span>
                        </div>
                        <p class="text-sm text-zinc-400 mb-4">{{ prj.desc }}</p>
                    </div>
                    
                    <div class="mt-4 pt-4 border-t border-zinc-800">
                        <h4 class="mono text-cyan-400 text-xs mb-3 uppercase font-bold">PROJECT INTEL FOLDERS</h4>
                        <div class="flex flex-wrap gap-2">
                            <a href="/project/{{ prj.id }}/folder/{{ username }}" target="_blank" class="btn-cyber px-4 py-2 mono text-xs font-bold bg-cyan-900/10">
                                [+] OPEN MY DOSSIER
                            </a>
                            {% if prj.id in folders %}
                                {% for f in folders[prj.id] %}
                                    {% if f.user != username %}
                                    <a href="/project/{{ prj.id }}/folder/{{ f.user }}" target="_blank" class="border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-400 px-3 py-2 mono text-[10px] transition-colors bg-black">
                                        VIEW: {{ db.users.get(f.user, {}).get('name', 'UNKNOWN') | upper }}
                                    </a>
                                    {% endif %}
                                {% endfor %}
                            {% endif %}
                        </div>
                    </div>

                    <div class="mt-6 pt-4 border-t border-zinc-800 flex justify-between items-center text-xs mono text-zinc-500">
                        <div>LEAD: <span class="text-cyan-400">{{ prj.lead }}</span></div>
                        {% if user.role in ['ceo', 'cofounder', 'admin'] %}
                        <form action="/delete_project" method="POST" onsubmit="return confirm('WARNING: PERMANENTLY TERMINATE THIS PROJECT DIRECTIVE?');">
                            <input type="hidden" name="project_id" value="{{ prj.id }}">
                            <button type="submit" class="px-3 py-1 border border-red-500 text-red-500 hover:bg-red-500 hover:text-white transition-colors">TERMINATE</button>
                        </form>
                        {% endif %}
                    </div>
                </div>
                {% else %}
                    <p class="mono text-sm text-zinc-600 col-span-2">NO ACCESSIBLE PROJECTS IN DATABANK.</p>
                {% endfor %}
            </div>
        </section>

        <!-- TAB: COMMS -->
        <section id="tab-comms" class="tab-content hidden">
            <h2 class="mono text-2xl text-cyan-400 mb-6 border-b border-zinc-800 pb-2 tracking-widest uppercase">ENCRYPTED COMMUNICATIONS</h2>
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[70vh]">
                <div class="cyber-border p-6 col-span-1 flex flex-col">
                    <h3 class="mono text-cyan-400 mb-4 uppercase">Transmit Signal</h3>
                    <form action="/send_message" method="POST" class="flex flex-col gap-4 flex-1">
                        <select name="receiver" class="input-cyber p-2 text-sm w-full" required>
                            <option value="">Select Recipient...</option>
                            {% for uname, udata in db.users.items() %}
                                {% if uname != username %}
                                <option value="{{ uname }}">{{ udata.name }} ({{ udata.clearance }})</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        <textarea name="content" class="input-cyber p-2 text-sm w-full flex-1 resize-none" placeholder="Enter encrypted payload..." required></textarea>
                        <button type="submit" class="btn-cyber py-2 mono text-sm font-bold">TRANSMIT</button>
                    </form>
                </div>
                <div class="cyber-border p-6 col-span-2 flex flex-col overflow-y-auto">
                    <h3 class="mono text-cyan-400 mb-4 uppercase">Signal Intercepts (Inbox)</h3>
                    <div class="space-y-4">
                        {% set ns = namespace(has_msgs=false) %}
                        {% for msg in db.messages %}
                            {% if msg.receiver == username or msg.sender == username %}
                                {% set ns.has_msgs = true %}
                                <div class="p-3 border {{ 'border-cyan-900 bg-cyan-950/20' if msg.receiver == username else 'border-zinc-800 bg-zinc-900/50' }} rounded relative">
                                    <div class="flex justify-between items-center mb-2 border-b border-zinc-800/50 pb-1">
                                        <span class="mono text-xs text-cyan-400">
                                            {% if msg.sender == username %}TO: {{ db.users.get(msg.receiver, {}).get('name', 'UNKNOWN') }}{% else %}FROM: {{ db.users.get(msg.sender, {}).get('name', 'UNKNOWN') }}{% endif %}
                                        </span>
                                        <span class="mono text-[10px] text-zinc-500">{{ msg.timestamp }}</span>
                                    </div>
                                    <p class="text-sm text-zinc-300">{{ msg.content }}</p>
                                </div>
                            {% endif %}
                        {% endfor %}
                        {% if not ns.has_msgs %}
                            <p class="mono text-sm text-zinc-600">NO INTERCEPTS FOUND.</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </section>

        <!-- TAB: TASKS -->
        <section id="tab-tasks" class="tab-content hidden">
            <h2 class="mono text-2xl text-cyan-400 mb-6 border-b border-zinc-800 pb-2 tracking-widest uppercase">DIRECTIVES & ASSIGNMENTS</h2>
            {% if user.role in ['ceo', 'admin', 'cofounder'] %}
            <div class="cyber-border p-6 mb-8 bg-[#0a0a0a]">
                <h3 class="mono text-red-500 mb-4 uppercase glow-red font-bold text-sm">COMMAND OVERRIDE: ISSUE DIRECTIVE</h3>
                <form action="/assign_task" method="POST" class="flex flex-col lg:flex-row gap-4">
                    <select name="assigned_to" class="input-cyber p-2 text-sm lg:w-1/4" required>
                        <option value="">Assign Personnel...</option>
                        {% for uname, udata in db.users.items() %}
                            <option value="{{ uname }}">{{ udata.name }} ({{ udata.role }})</option>
                        {% endfor %}
                    </select>
                    <input type="text" name="description" class="input-cyber p-2 text-sm flex-1" placeholder="Directive details..." required>
                    <button type="submit" class="btn-cyber btn-red py-2 px-6 mono text-sm font-bold">AUTHORIZE</button>
                </form>
            </div>
            {% endif %}
            <div class="grid grid-cols-1 gap-4">
                <h3 class="mono text-zinc-400 uppercase text-sm mb-2">My Directives</h3>
                {% set ts = namespace(has_tasks=false) %}
                {% for task in db.tasks %}
                    {% if task.assigned_to == username or user.role in ['ceo', 'admin'] %}
                        {% set ts.has_tasks = true %}
                        <div class="cyber-border p-4 flex justify-between items-center border-l-4 {{ 'border-l-cyan-500' if task.assigned_to == username else 'border-l-zinc-700' }}">
                            <div>
                                <span class="mono text-xs text-zinc-500 block mb-1">ISSUED BY: {{ db.users.get(task.assigned_by, {}).get('name', 'UNKNOWN') }} &nbsp;|&nbsp; ASSIGNED TO: <span class="text-cyan-400">{{ db.users.get(task.assigned_to, {}).get('name', 'UNKNOWN') }}</span></span>
                                <p class="text-zinc-200">{{ task.description }}</p>
                            </div>
                            <div>
                                <span class="mono text-xs px-2 py-1 border border-[#00ff41] text-[#00ff41] bg-[#00ff41]/10 uppercase">{{ task.status }}</span>
                            </div>
                        </div>
                    {% endif %}
                {% endfor %}
                {% if not ts.has_tasks %}
                    <p class="mono text-sm text-zinc-600">NO ACTIVE DIRECTIVES.</p>
                {% endif %}
            </div>
        </section>

        <!-- TAB: REPORTS -->
        <section id="tab-reports" class="tab-content hidden">
            <h2 class="mono text-2xl text-cyan-400 mb-6 border-b border-zinc-800 pb-2 tracking-widest uppercase">DAILY REPORT LOG</h2>
            <div class="cyber-border p-6 mb-8">
                <h3 class="mono text-cyan-400 mb-4 uppercase text-sm">Submit Status Report</h3>
                <form action="/submit_report" method="POST" class="flex flex-col gap-4">
                    <textarea name="content" class="input-cyber p-3 text-sm w-full resize-none h-24" placeholder="Log daily activities, facility updates, or anomalies..." required></textarea>
                    <div class="flex justify-end">
                        <button type="submit" class="btn-cyber py-2 px-8 mono text-sm font-bold">LOG REPORT</button>
                    </div>
                </form>
            </div>
            <div class="space-y-4">
                <h3 class="mono text-zinc-400 uppercase text-sm mb-2">Facility Logbook</h3>
                {% for rep in db.reports %}
                <div class="cyber-border p-4 bg-[#080808]">
                    <div class="flex justify-between items-center mb-2 border-b border-zinc-800/50 pb-2">
                        <span class="mono text-sm text-cyan-400 font-bold">{{ db.users.get(rep.user, {}).get('name', 'UNKNOWN') }} <span class="text-zinc-500 text-xs">({{ db.users.get(rep.user, {}).get('role', 'Terminated') }})</span></span>
                        <span class="mono text-[10px] text-[#00ff41]">{{ rep.date }}</span>
                    </div>
                    <p class="text-sm text-zinc-300 leading-relaxed">{{ rep.content }}</p>
                </div>
                {% else %}
                    <p class="mono text-sm text-zinc-600">NO LOGS RECORDED YET.</p>
                {% endfor %}
            </div>
        </section>

        <!-- TAB: ADMIN -->
        {% if user.role == 'admin' %}
        <section id="tab-admin" class="tab-content hidden">
            <h2 class="mono text-2xl text-red-500 mb-6 border-b border-red-900 pb-2 tracking-widest uppercase glow-red">SYSTEM ADMINISTRATION</h2>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="cyber-border p-6 border-red-900 bg-red-950/10">
                    <h3 class="mono text-red-400 mb-4 uppercase text-sm">Provision New Identity</h3>
                    <form action="/admin/add_user" method="POST" class="space-y-4">
                        <div>
                            <label class="mono text-xs text-zinc-400 uppercase block mb-1">Full Name</label>
                            <input type="text" name="name" class="input-cyber border-red-900 w-full p-2 text-sm" required>
                        </div>
                        <div class="flex gap-4">
                            <div class="flex-1">
                                <label class="mono text-xs text-zinc-400 uppercase block mb-1">System ID</label>
                                <input type="text" name="new_username" class="input-cyber border-red-900 w-full p-2 text-sm" required>
                            </div>
                            <div class="flex-1">
                                <label class="mono text-xs text-zinc-400 uppercase block mb-1">Passcode</label>
                                <input type="password" name="new_password" class="input-cyber border-red-900 w-full p-2 text-sm" required>
                            </div>
                        </div>
                        <div>
                            <label class="mono text-xs text-zinc-400 uppercase block mb-1">Clearance Role</label>
                            <select name="role" class="input-cyber border-red-900 w-full p-2 text-sm" required>
                                <option value="employee">Employee (L1)</option>
                                <option value="researcher">Researcher (L2)</option>
                                <option value="scientist">Scientist (L3)</option>
                                <option value="cofounder">Co-Founder (L4)</option>
                                <option value="ceo">CEO (L5)</option>
                            </select>
                        </div>
                        <div class="pt-2">
                            <label class="flex items-center space-x-2 cursor-pointer border border-red-900/50 p-2 bg-black hover:bg-zinc-900">
                                <input type="checkbox" name="ts_access" value="1" class="w-4 h-4 accent-red-600 bg-black">
                                <span class="mono text-xs text-red-500 font-bold uppercase glow-red">Grant Top Secret Access</span>
                            </label>
                        </div>
                        <button type="submit" class="btn-cyber btn-red w-full py-2 mono text-sm font-bold mt-2">EXECUTE CREATION</button>
                    </form>
                </div>
                <div class="cyber-border p-6 border-red-900 bg-red-950/10 overflow-y-auto max-h-[60vh]">
                    <h3 class="mono text-red-400 mb-4 uppercase text-sm">Active Identities</h3>
                    <div class="space-y-3">
                        {% for uname, udata in db.users.items() %}
                        <div class="p-3 border border-red-900/50 bg-black flex justify-between items-center">
                            <div>
                                <div class="mono text-sm text-cyan-400">{{ udata.name }}</div>
                                <div class="mono text-xs text-zinc-500">ID: {{ uname }} | ROLE: {{ udata.role | upper }}</div>
                            </div>
                            <div class="flex space-x-2">
                                {% if uname != 'admin' %}
                                <form action="/admin/toggle_ts" method="POST">
                                    <input type="hidden" name="username" value="{{ uname }}">
                                    <button type="submit" class="px-2 py-1 mono text-[10px] border transition-colors {{ 'border-red-500 text-red-500 bg-red-900/20 glow-red' if udata.ts_access else 'border-zinc-700 text-zinc-500 hover:text-white' }}">
                                        TS: {{ 'GRANTED' if udata.ts_access else 'DENIED' }}
                                    </button>
                                </form>
                                <form action="/admin/remove_user" method="POST" onsubmit="return confirm('TERMINATE USER IDENTITY?');">
                                    <input type="hidden" name="del_username" value="{{ uname }}">
                                    <button type="submit" class="px-2 py-1 border border-zinc-700 text-zinc-500 hover:bg-red-600 hover:text-white hover:border-red-600 mono text-[10px] transition-colors">DEL</button>
                                </form>
                                {% else %}
                                <span class="mono text-xs text-red-700">PROTECTED</span>
                                {% endif %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </section>
        {% endif %}
    </main>
</div>

<script>
    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
        document.querySelectorAll('.nav-btn').forEach(el => {
            el.classList.remove('border-cyan-400', 'text-cyan-400');
            if(!el.id.includes('admin')) {
                el.classList.add('border-transparent', 'text-zinc-400');
            }
        });
        document.getElementById('tab-' + tabId).classList.remove('hidden');
        const activeNav = document.getElementById('nav-' + tabId);
        if(activeNav && !tabId.includes('admin')) {
            activeNav.classList.remove('border-transparent', 'text-zinc-400');
            activeNav.classList.add('border-cyan-400', 'text-cyan-400');
        }
    }
    document.addEventListener("DOMContentLoaded", () => {
        switchTab('projects');
    });
</script>
"""

FOLDER_HTML = """
<div class="h-screen flex flex-col p-8 max-w-5xl mx-auto relative z-10 w-full">
    <div class="flex justify-between items-end border-b-2 border-cyan-900 pb-4 mb-6">
        <div>
            <h1 class="mono text-3xl text-cyan-400 glow-text font-bold tracking-widest">PROJECT DOSSIER</h1>
            <p class="mono text-sm text-zinc-400 mt-2 uppercase">ID: {{ project.id }} &nbsp;|&nbsp; TITLE: <span class="text-zinc-200">{{ project.title }}</span></p>
        </div>
        <div class="text-right">
            <h2 class="mono text-xl text-zinc-200 uppercase font-bold">AUTHOR: {{ target_user_data.name if target_user_data else 'UNKNOWN' }}</h2>
            <p class="mono text-xs text-zinc-500 mt-1">LAST SYNC: {{ folder.date if folder else 'NO DATA' }}</p>
        </div>
    </div>
    
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="mb-4 p-3 border border-[#00ff41] bg-[#00ff41]/10 text-[#00ff41] mono text-sm shadow-[0_0_10px_rgba(0,255,65,0.2)] text-center font-bold">
          SYSTEM NOTICE: {{ messages[0] }}
        </div>
      {% endif %}
    {% endwith %}

    {% if is_owner %}
    <form action="/save_folder" method="POST" class="flex-1 flex flex-col min-h-0">
        <input type="hidden" name="project_id" value="{{ project.id }}">
        <textarea name="content" class="flex-1 bg-[#0a0a0a] text-zinc-200 border border-zinc-800 p-8 font-mono text-[15px] resize-none focus:border-cyan-500 focus:shadow-[0_0_15px_rgba(0,229,255,0.1)] outline-none leading-relaxed w-full shadow-inner custom-scrollbar" placeholder="Commence documentation log here. Type as much as needed; this folder dynamically expands to hold massive data sets...">{{ folder.content if folder else '' }}</textarea>
        
        <div class="mt-6 flex justify-between items-center">
            <span class="mono text-xs text-cyan-600 font-bold tracking-widest uppercase">💾 Storage Capacity: Unlimited</span>
            <div class="space-x-4">
                <button type="button" onclick="window.close()" class="border border-zinc-700 text-zinc-400 hover:text-white px-6 py-3 mono text-sm font-bold transition-colors">CLOSE FOLDER</button>
                <button type="submit" class="btn-cyber py-3 px-8 text-sm font-bold shadow-lg">ENCRYPT & SAVE DOSSIER</button>
            </div>
        </div>
    </form>
    {% else %}
    <div class="flex-1 bg-[#0a0a0a] text-zinc-300 border border-zinc-800 p-8 font-mono text-[15px] overflow-y-auto leading-relaxed w-full shadow-inner whitespace-pre-wrap">{{ folder.content if folder else 'NO DATA LOGGED BY THIS AUTHOR.' }}</div>
    <div class="mt-6 flex justify-between items-center">
        <span class="mono text-xs text-red-500 uppercase glow-red font-bold">READ ONLY / WRITE ACCESS DENIED</span>
        <button onclick="window.close()" class="border border-zinc-700 text-zinc-400 hover:text-white px-8 py-3 mono text-sm font-bold transition-colors">CLOSE FOLDER</button>
    </div>
    {% endif %}
</div>
"""

# --- FLASK ROUTES ---

def login_required(f):
    def wrap(*args, **kwargs):
        # Prevent ghost sessions if a user was deleted while logged in.
        if 'username' not in session:
            return redirect(url_for('index'))
            
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE id=?", (session['username'],)).fetchone()
        conn.close()
        
        if not user:
            session.clear()
            return redirect(url_for('index'))
            
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    template = BASE_HTML.replace('[[CONTENT_PLACEHOLDER]]', LOGIN_HTML)
    return render_template_string(template)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ? AND password = ?", (username, password)).fetchone()
    if user:
        session['username'] = user['id']
        session['role'] = user['role']
        conn.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", 
                     (str(uuid.uuid4())[:8], 'admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"SYSTEM EVENT: Secure handshake established by ID: {username}."))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    else:
        conn.close()
        flash("ACCESS DENIED. INVALID CREDENTIALS.")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    conn = get_db()
    
    # Session is already verified by @login_required, safe to fetch
    user_data = conn.execute("SELECT * FROM users WHERE id = ?", (username,)).fetchone()
    users_raw = conn.execute("SELECT * FROM users").fetchall()
    db_users = {u['id']: dict(u) for u in users_raw}
    
    projects_raw = conn.execute("SELECT * FROM projects ORDER BY ts_access DESC").fetchall()
    visible_projects = [p for p in projects_raw if p['ts_access'] == 0 or user_data['ts_access'] == 1]
    
    messages = conn.execute("SELECT * FROM messages ORDER BY timestamp DESC").fetchall()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    reports = conn.execute("SELECT * FROM reports ORDER BY date DESC").fetchall()
    
    contribs_raw = conn.execute("SELECT project_id, user FROM contributions").fetchall()
    folders = {}
    for c in contribs_raw:
        pid = c['project_id']
        if pid not in folders: folders[pid] = []
        folders[pid].append(c)
        
    conn.close()
    
    context = {
        'users': db_users,
        'projects': visible_projects,
        'messages': messages,
        'tasks': tasks,
        'reports': reports
    }
    
    template = BASE_HTML.replace('[[CONTENT_PLACEHOLDER]]', DASHBOARD_HTML)
    return render_template_string(template, username=username, user=user_data, db=context, folders=folders)

@app.route('/create_project', methods=['POST'])
@login_required
def create_project():
    if session['role'] not in ['ceo', 'cofounder', 'admin']:
        return redirect(url_for('dashboard'))
    title = request.form.get('title')
    desc = request.form.get('desc')
    status = request.form.get('status', 'Active')
    ts_access = 1 if request.form.get('ts_access') else 0
    if title and desc:
        prj_id = f"PRJ-{random.randint(100, 999)}"
        conn = get_db()
        lead_name = conn.execute("SELECT name FROM users WHERE id=?", (session['username'],)).fetchone()['name']
        conn.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", (prj_id, title, desc, status, lead_name, ts_access))
        conn.commit()
        conn.close()
        flash(f"Project Directive {prj_id} initialized.")
    return redirect(url_for('dashboard'))

@app.route('/delete_project', methods=['POST'])
@login_required
def delete_project():
    if session['role'] not in ['ceo', 'cofounder', 'admin']:
        return redirect(url_for('dashboard'))
    project_id = request.form.get('project_id')
    conn = get_db()
    conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.execute("DELETE FROM contributions WHERE project_id=?", (project_id,))
    conn.commit()
    conn.close()
    flash(f"Project {project_id} permanently terminated.")
    return redirect(url_for('dashboard'))

@app.route('/project/<project_id>/folder/<target_user>')
@login_required
def view_folder(project_id, target_user):
    conn = get_db()
    proj = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    current_user = conn.execute("SELECT * FROM users WHERE id=?", (session['username'],)).fetchone()
    target_user_data = conn.execute("SELECT * FROM users WHERE id=?", (target_user,)).fetchone()
    
    if not proj:
        conn.close()
        abort(404)
        
    if proj['ts_access'] == 1 and current_user['ts_access'] == 0:
        conn.close()
        abort(403)
        
    folder = conn.execute("SELECT * FROM contributions WHERE project_id=? AND user=?", (project_id, target_user)).fetchone()
    conn.close()
    
    is_owner = (target_user == session['username'])
    template = BASE_HTML.replace('[[CONTENT_PLACEHOLDER]]', FOLDER_HTML)
    return render_template_string(template, project=proj, target_user_data=target_user_data, folder=folder, is_owner=is_owner)

@app.route('/save_folder', methods=['POST'])
@login_required
def save_folder():
    pid = request.form.get('project_id')
    content = request.form.get('content')
    uid = session['username']
    conn = get_db()
    proj = conn.execute("SELECT ts_access FROM projects WHERE id=?", (pid,)).fetchone()
    user = conn.execute("SELECT ts_access FROM users WHERE id=?", (uid,)).fetchone()
    
    if proj and (proj['ts_access'] == 0 or user['ts_access'] == 1):
        existing = conn.execute("SELECT id FROM contributions WHERE project_id=? AND user=?", (pid, uid)).fetchone()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if existing:
            conn.execute("UPDATE contributions SET content=?, date=? WHERE id=?", (content, now, existing['id']))
        else:
            conn.execute("INSERT INTO contributions VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4())[:8], pid, uid, now, content))
        conn.commit()
        flash("Dossier successfully updated and encrypted.")
    else:
        flash("ACCESS DENIED: Insufficient clearance.")
    conn.close()
    return redirect(url_for('view_folder', project_id=pid, target_user=uid))

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver = request.form.get('receiver')
    content = request.form.get('content')
    if receiver and content:
        conn = get_db()
        conn.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4())[:8], session['username'], receiver, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        flash("Encrypted signal transmitted successfully.")
    return redirect(url_for('dashboard'))

@app.route('/assign_task', methods=['POST'])
@login_required
def assign_task():
    if session['role'] not in ['ceo', 'admin', 'cofounder']:
        return redirect(url_for('dashboard'))
    assigned_to = request.form.get('assigned_to')
    description = request.form.get('description')
    if assigned_to and description:
        conn = get_db()
        conn.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4())[:8], session['username'], assigned_to, description, "PENDING"))
        conn.commit()
        conn.close()
        flash(f"Directive assigned to {assigned_to}.")
    return redirect(url_for('dashboard'))

@app.route('/submit_report', methods=['POST'])
@login_required
def submit_report():
    content = request.form.get('content')
    if content:
        conn = get_db()
        conn.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (str(uuid.uuid4())[:8], session['username'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), content))
        conn.commit()
        conn.close()
        flash("Logbook updated successfully.")
    return redirect(url_for('dashboard'))

@app.route('/admin/add_user', methods=['POST'])
@login_required
def add_user():
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    name = request.form.get('name')
    role = request.form.get('role')
    ts_access = 1 if request.form.get('ts_access') else 0
    clearance_map = { "employee": "LEVEL 1", "researcher": "LEVEL 2", "scientist": "LEVEL 3", "cofounder": "LEVEL 4", "ceo": "LEVEL 5" }
    
    if new_user and new_pass:
        conn = get_db()
        try:
            conn.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (new_user, new_pass, role, name, clearance_map.get(role, "LEVEL 1"), ts_access))
            conn.commit()
            flash(f"Identity {new_user} provisioned.")
        except sqlite3.IntegrityError:
            flash("ERROR: System ID already in use.")
        finally:
            conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/toggle_ts', methods=['POST'])
@login_required
def toggle_ts():
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    target = request.form.get('username')
    conn = get_db()
    user = conn.execute("SELECT ts_access FROM users WHERE id=?", (target,)).fetchone()
    if user and target != 'admin':
        new_val = 0 if user['ts_access'] == 1 else 1
        conn.execute("UPDATE users SET ts_access=? WHERE id=?", (new_val, target))
        conn.commit()
        flash(f"Top Secret access updated for {target}.")
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin/remove_user', methods=['POST'])
@login_required
def remove_user():
    if session['role'] != 'admin':
        return redirect(url_for('dashboard'))
    del_user = request.form.get('del_username')
    if del_user != 'admin':
        conn = get_db()
        conn.execute("DELETE FROM users WHERE id=?", (del_user,))
        conn.commit()
        conn.close()
        flash(f"Identity {del_user} terminated.")
    return redirect(url_for('dashboard'))



def keep_alive_ping():
    """Sends a ping to the server every 15 minutes (900 seconds)"""
    while True:
        try:
            # Send a simple GET request
            urllib.request.urlopen("https://www.com", timeout=10)
            print("[SYSTEM] Ping sent to myserver.com")
        except Exception as e:
            print(f"[SYSTEM] Ping failed: {e}")
        
        # Wait for 15 minutes (15 * 60 = 900 seconds)
        time.sleep(900)


if __name__ == '__main__':
    # Start the background ping thread
    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()
    
    # Start Flask
    app.run(debug=True, port=5000)
    
    
