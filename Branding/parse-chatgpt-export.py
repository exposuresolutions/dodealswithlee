"""
ChatGPT Export Parser — Backup memories & conversations
========================================================
Drop the ChatGPT export zip into this folder and run.
Extracts memories and conversation summaries.
"""
import json
import zipfile
import sys
from pathlib import Path
from datetime import datetime

EXPORT_DIR = Path(__file__).parent.parent / "chatgpt-backup"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def find_export_zip():
    """Find the ChatGPT export zip in Downloads or current dir."""
    search_dirs = [
        Path.home() / "Downloads",
        Path(__file__).parent,
        Path(__file__).parent.parent,
    ]
    for d in search_dirs:
        for f in sorted(d.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
            if "chatgpt" in f.name.lower() or "openai" in f.name.lower() or "2026" in f.name:
                return f
    return None


def parse_export(zip_path):
    """Parse the ChatGPT export zip."""
    print(f"  Parsing: {zip_path.name}")

    with zipfile.ZipFile(zip_path, 'r') as z:
        names = z.namelist()
        print(f"  Files in zip: {len(names)}")

        # Extract memories
        memory_files = [n for n in names if 'memory' in n.lower()]
        if memory_files:
            print(f"\n  MEMORIES ({len(memory_files)} files)")
            print("  " + "-" * 50)
            all_memories = []
            for mf in memory_files:
                data = json.loads(z.read(mf))
                if isinstance(data, list):
                    all_memories.extend(data)
                elif isinstance(data, dict):
                    all_memories.append(data)

            # Save memories
            mem_file = EXPORT_DIR / "chatgpt-memories.json"
            mem_file.write_text(json.dumps(all_memories, indent=2))
            print(f"  ✅ Saved {len(all_memories)} memories → {mem_file.name}")

            # Also save as readable text
            txt_file = EXPORT_DIR / "chatgpt-memories.txt"
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f"ChatGPT Memory Backup — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"{'='*60}\n\n")
                for i, mem in enumerate(all_memories, 1):
                    if isinstance(mem, dict):
                        content = mem.get('content', mem.get('memory', mem.get('text', str(mem))))
                        created = mem.get('created_at', mem.get('timestamp', 'unknown'))
                        f.write(f"{i}. [{created}] {content}\n\n")
                    else:
                        f.write(f"{i}. {mem}\n\n")
            print(f"  ✅ Readable backup → {txt_file.name}")
        else:
            print("  ⚠️ No memory files found in export")

        # Extract conversations summary
        conv_files = [n for n in names if 'conversation' in n.lower() and n.endswith('.json')]
        if conv_files:
            print(f"\n  CONVERSATIONS ({len(conv_files)} files)")
            print("  " + "-" * 50)
            all_convs = []
            for cf in conv_files:
                try:
                    data = json.loads(z.read(cf))
                    if isinstance(data, list):
                        all_convs.extend(data)
                    elif isinstance(data, dict):
                        all_convs.append(data)
                except:
                    pass

            # Save full conversations
            conv_file = EXPORT_DIR / "chatgpt-conversations.json"
            conv_file.write_text(json.dumps(all_convs, indent=2))
            print(f"  ✅ Saved {len(all_convs)} conversations → {conv_file.name}")

            # Save summary
            summary_file = EXPORT_DIR / "chatgpt-conversation-summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"ChatGPT Conversation Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"{'='*60}\n\n")
                for conv in all_convs:
                    if isinstance(conv, dict):
                        title = conv.get('title', 'Untitled')
                        created = conv.get('create_time', conv.get('created_at', ''))
                        if isinstance(created, (int, float)):
                            created = datetime.fromtimestamp(created).strftime('%Y-%m-%d')
                        msg_count = len(conv.get('mapping', {}))
                        f.write(f"  [{created}] {title} ({msg_count} messages)\n")
            print(f"  ✅ Summary → {summary_file.name}")
        else:
            print("  ⚠️ No conversation files found")

        # Extract everything else
        z.extractall(EXPORT_DIR / "raw")
        print(f"\n  ✅ Full raw export → {EXPORT_DIR / 'raw'}")


def main():
    print("=" * 60)
    print("  ChatGPT Export Parser")
    print("=" * 60)

    # Check for zip path argument
    if len(sys.argv) > 1:
        zip_path = Path(sys.argv[1])
    else:
        zip_path = find_export_zip()

    if not zip_path or not zip_path.exists():
        print("\n  ❌ No ChatGPT export zip found.")
        print("  Either:")
        print("    1. Download from ChatGPT → Settings → Data Controls → Export")
        print("    2. Run: python parse-chatgpt-export.py path/to/export.zip")
        return

    parse_export(zip_path)

    print(f"\n{'='*60}")
    print(f"  All backed up to: {EXPORT_DIR}")
    print(f"  Safe to clear ChatGPT memory now!")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
