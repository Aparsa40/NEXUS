
import os
import re
import json
import base64
import logging
from typing import Optional, Tuple

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# ============================================================
# 1. CONFIGURATION
# ============================================================

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

GITHUB_REPO = os.getenv("GITHUB_REPO", "Aparsa40/Rudin-store")

# Default OpenRouter model.
# You can change this to "openrouter/free" for automatic
# selection among currently available free models.
AI_MODEL = os.getenv(
    "AI_MODEL",
    "meta-llama/llama-3-8b-instruct:free"
)

GITHUB_API_BASE = "https://api.github.com"
OPENROUTER_API_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

MAX_DISCORD_MESSAGE = 1900
MAX_AI_OUTPUT = 12000

# ============================================================
# 2. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("WifreamAI")


# ============================================================
# 3. ENVIRONMENT VALIDATION
# ============================================================

required_variables = {
    "DISCORD_TOKEN": DISCORD_TOKEN,
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
}

missing_variables = [
    name for name, value in required_variables.items()
    if not value
]

if missing_variables:
    raise RuntimeError(
        "Missing environment variables: "
        + ", ".join(missing_variables)
    )

# ============================================================
# 4. DISCORD INITIALIZATION
# ============================================================

intents = discord.Intents.default()

# Required for reading normal messages and prefix commands.
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

http_session: Optional[aiohttp.ClientSession] = None


# ============================================================
# 5. HTTP SESSION MANAGEMENT
# ============================================================

async def get_session() -> aiohttp.ClientSession:
    """Create or reuse the shared asynchronous HTTP session."""

    global http_session

    if http_session is None or http_session.closed:
        http_session = aiohttp.ClientSession(
            timeout=REQUEST_TIMEOUT
        )

    return http_session


async def close_session():
    """Close the shared HTTP session safely."""

    global http_session

    if http_session and not http_session.closed:
        await http_session.close()

    http_session = None


# ============================================================
# 6. GITHUB API
# ============================================================

def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_file_url(filepath: str) -> str:
    """Build the correct GitHub Contents API URL."""

    safe_path = "/".join(
        aiohttp.helpers.quote(part, safe="")
        for part in filepath.strip("/").split("/")
    )

    return (
        f"{GITHUB_API_BASE}/repos/"
        f"{GITHUB_REPO}/contents/{safe_path}"
    )


async def get_github_file(
    filepath: str
) -> Tuple[Optional[str], Optional[str]]:
    """Read a repository file and return its content and SHA."""

    url = github_file_url(filepath)
    session = await get_session()

    try:
        async with session.get(
            url,
            headers=github_headers()
        ) as response:

            if response.status == 200:
                data = await response.json()

                if data.get("encoding") != "base64":
                    logger.error(
                        "Unsupported GitHub file encoding."
                    )
                    return None, None

                raw_content = base64.b64decode(
                    data["content"]
                )

                content = raw_content.decode("utf-8")

                return content, data["sha"]

            error_text = await response.text()

            logger.error(
                "GitHub read failed: %s | %s",
                response.status,
                error_text[:500]
            )

    except Exception:
        logger.exception("GitHub file read error")

    return None, None


async def update_github_file(
    filepath: str,
    content: str,
    sha: str,
    commit_message: str = "Updated by Wifream-AI"
) -> bool:
    """Update a file through GitHub Contents API."""

    url = github_file_url(filepath)
    session = await get_session()

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("ascii")

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "sha": sha,
        "branch": "main",
    }

    try:
        async with session.put(
            url,
            headers=github_headers(),
            json=payload
        ) as response:

            if response.status in (200, 201):
                logger.info(
                    "GitHub file updated: %s",
                    filepath
                )
                return True

            error_text = await response.text()

            logger.error(
                "GitHub update failed: %s | %s",
                response.status,
                error_text[:500]
            )

    except Exception:
        logger.exception("GitHub update error")

    return False


# ============================================================
# 7. GITHUB PROJECT STATUS
# ============================================================

async def get_github_data(endpoint: str):
    """Fetch JSON data from GitHub REST API."""

    session = await get_session()

    url = f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/{endpoint}"

    try:
        async with session.get(
            url,
            headers=github_headers()
        ) as response:

            if response.status == 200:
                return await response.json()

            logger.error(
                "GitHub API error: %s",
                response.status
            )

    except Exception:
        logger.exception("GitHub API request failed")

    return None


async def get_project_status() -> str:
    """Collect latest commits, branches and open pull requests."""

    commits = await get_github_data(
        "commits?per_page=5"
    )

    branches = await get_github_data(
        "branches?per_page=100"
    )

    pull_requests = await get_github_data(
        "pulls?state=open&per_page=20"
    )

    if commits is None or branches is None or pull_requests is None:
        return "❌ دریافت اطلاعات GitHub کامل نشد. گزارش قابل اعتماد نیست."

    lines = [
        "📊 **Rudin Store — GitHub Status**",
        f"📦 Repository: `{GITHUB_REPO}`",
        ""
    ]

    lines.append("**آخرین Commitها:**")

    for commit in commits:
        message = commit["commit"]["message"].split("\n")[0]

        sha = commit["sha"][:7]

        lines.append(
            f"• `{sha}` {message[:120]}"
        )

    lines.append("")
    lines.append(
        f"🌿 تعداد Branchها: {len(branches)}"
    )

    lines.append("")
    lines.append(
        f"🔀 تعداد PRهای باز: {len(pull_requests)}"
    )

    for pr in pull_requests[:10]:
        lines.append(
            f"• PR #{pr['number']}: "
            f"{pr['title'][:100]}"
        )

        lines.append(
            f"  وضعیت: {pr['html_url']}"
        )

    lines.append("")
    lines.append(
        "🔗 https://github.com/"
        + GITHUB_REPO
    )

    return "\n".join(lines)


# ============================================================
# 8. OPENROUTER AI
# ============================================================

async def ask_ai(
    prompt: str,
    system_prompt: str = (
        "You are Wifream-AI, a senior software engineer, "
        "AI assistant and project development expert. "
        "Provide accurate, structured and practical answers."
    )
) -> str:
    """Send a chat completion request to OpenRouter."""

    session = await get_session()

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://discord.com",
        "X-Title": "Wifream-AI",
    }

    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 3000,
    }

    try:
        async with session.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload
        ) as response:

            response_data = await response.json(
                content_type=None
            )

            if response.status == 200:
                choices = response_data.get("choices", [])

                if not choices:
                    return "❌ مدل پاسخ معتبری برنگرداند."

                return (
                    choices[0]
                    .get("message", {})
                    .get("content", "")
                    or "مدل پاسخ متنی برنگرداند."
                )

            logger.error(
                "OpenRouter error: %s | %s",
                response.status,
                json.dumps(
                    response_data,
                    ensure_ascii=False
                )[:1000]
            )

            error_message = response_data.get(
                "error", {}
            )

            if isinstance(error_message, dict):
                error_message = error_message.get(
                    "message",
                    str(error_message)
                )

            return (
                f"❌ خطای OpenRouter ({response.status}): "
                f"{str(error_message)[:700]}"
            )

    except Exception as error:
        logger.exception("OpenRouter request failed")

        return (
            "❌ خطای ارتباط با OpenRouter: "
            + str(error)
        )


# ============================================================
# 9. DISCORD MESSAGE UTILITIES
# ============================================================

async def send_long_message(ctx, content: str):
    """Split long messages to fit Discord message limits."""

    if not content:
        await ctx.send("پاسخی برای ارسال وجود ندارد.")
        return

    for index in range(0, len(content), MAX_DISCORD_MESSAGE):
        await ctx.send(
            content[index:index + MAX_DISCORD_MESSAGE]
        )


# ============================================================
# 10. BOT EVENTS
# ============================================================

@bot.event
async def on_ready():
    logger.info(
        "Wifream-AI is online as %s",
        bot.user
    )

    logger.info(
        "Connected to %s Discord servers",
        len(bot.guilds)
    )

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="!help | AI Project Assistant"
        )
    )


@bot.event
async def on_message(message):
    """Process normal messages and prefix commands."""

    if message.author.bot:
        return

    # Let prefix commands be processed first.
    await bot.process_commands(message)

    # Respond to direct mentions.
    if bot.user and bot.user.mentioned_in(message):
        prompt = re.sub(
            rf"<@!?{bot.user.id}>",
            "",
            message.content
        ).strip()

        if not prompt:
            prompt = "سلام! خودت را معرفی کن."

        async with message.channel.typing():
            answer = await ask_ai(prompt)

        await send_long_message(
            message.channel,
            answer
        )


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors without silently ignoring them."""

    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"❌ آرگومان موردنیاز وارد نشده است: `{error.param.name}`"
        )
        return

    if isinstance(error, commands.CommandInvokeError):
        logger.exception(
            "Command execution error",
            exc_info=error.original
        )

    else:
        logger.exception("Discord command error")

    await ctx.send(
        "❌ هنگام اجرای دستور خطایی رخ داد. "
        "ترمینال VS Code را بررسی کن."
    )


# ============================================================
# 11. DISCORD COMMANDS
# ============================================================

@bot.command(name="help")
async def help_command(ctx):

    help_text = """
🤖 **Wifream-AI Commands**

**AI Assistant**
`!ask سوال`
یا با Mention کردن ربات سؤال بپرس.

**GitHub**
`!خواندکد README.md`
`!status`
`!branches`
`!prs`
`!commits`

**Code Operations**
`!تغییر README.md توضیح تغییر`

**General**
`!help`
`!ping`
"""

    await ctx.send(help_text)


@bot.command(name="ping")
async def ping_command(ctx):

    latency = round(
        bot.latency * 1000
    )

    await ctx.send(
        f"🏓 Pong! Latency: `{latency}ms`"
    )


@bot.command(name="ask")
async def ask_command(
    ctx,
    *,
    prompt: str
):
    async with ctx.typing():

        answer = await ask_ai(prompt)

    await send_long_message(
        ctx,
        answer
    )


@bot.command(name="خواندکد")
async def read_code(
    ctx,
    *,
    filepath: str
):
    await ctx.send(
        f"🔄 در حال خواندن `{filepath}` از GitHub..."
    )

    content, _ = await get_github_file(filepath)

    if content is None:
        await ctx.send(
            "❌ فایل پیدا نشد یا دسترسی GitHub ناموفق بود."
        )
        return

    if len(content) > 1500:
        content = content[:1500] + "\n... (بقیه فایل حذف شده است)"

    await send_long_message(
        ctx,
        f"📄 **{filepath}**\n```text\n{content}\n```"
    )


@bot.command(name="status")
async def status_command(ctx):

    async with ctx.typing():

        status = await get_project_status()

    await send_long_message(
        ctx,
        status
    )


@bot.command(name="branches")
async def branches_command(ctx):

    async with ctx.typing():

        branches = await get_github_data(
            "branches?per_page=100"
        )

    if branches is None:
        await ctx.send("❌ دریافت Branchها ناموفق بود.")
        return

    lines = [
        "🌿 **GitHub Branches**",
        ""
    ]

    for branch in branches:
        lines.append(
            f"• `{branch['name']}`"
        )

    await send_long_message(
        ctx,
        "\n".join(lines)
    )


@bot.command(name="prs")
async def prs_command(ctx):

    async with ctx.typing():

        pull_requests = await get_github_data(
            "pulls?state=open&per_page=30"
        )

    if pull_requests is None:
        await ctx.send("❌ دریافت Pull Requestها ناموفق بود.")
        return

    if not pull_requests:
        await ctx.send("هیچ PR بازی وجود ندارد.")
        return

    lines = [
        "🔀 **Open Pull Requests**",
        ""
    ]

    for pr in pull_requests:
        lines.append(
            f"• **#{pr['number']}** {pr['title']}"
        )

        lines.append(
            pr["html_url"]
        )

    await send_long_message(
        ctx,
        "\n".join(lines)
    )


@bot.command(name="commits")
async def commits_command(ctx):

    async with ctx.typing():

        commits = await get_github_data(
            "commits?per_page=10"
        )

    if commits is None:
        await ctx.send("❌ دریافت Commitها ناموفق بود.")
        return

    lines = [
        "📝 **Latest GitHub Commits**",
        ""
    ]

    for commit in commits:
        sha = commit["sha"][:7]

        message = commit["commit"]["message"].split("\n")[0]

        url = commit["html_url"]

        lines.append(
            f"• `{sha}` {message}\n{url}"
        )

    await send_long_message(
        ctx,
        "\n".join(lines)
    )


# ============================================================
# 12. AI-ASSISTED GITHUB FILE EDITING
# ============================================================

@bot.command(name="تغییر")
async def edit_code(
    ctx,
    filepath: str,
    *,
    instruction: str
):
    """
    Generate a modified file using AI and update GitHub.

    IMPORTANT:
    This command currently writes directly to the main branch.
    Use only after reviewing the AI-generated content.
    """

    await ctx.send(
        f"⚙️ در حال خواندن `{filepath}` از GitHub..."
    )

    current_code, sha = await get_github_file(
        filepath
    )

    if current_code is None or sha is None:
        await ctx.send(
            "❌ نتوانستم فایل را از GitHub دریافت کنم."
        )
        return

    system_prompt = (
        "You are an expert software engineer. "
        "Modify the provided source file according to the user's instructions. "
        "Preserve existing functionality and unrelated code. "
        "Return ONLY the complete updated file content. "
        "Do not include Markdown code fences or explanations."
    )

    prompt = (
        f"Current file: {filepath}\n\n"
        f"Current code:\n{current_code}\n\n"
        f"Instructions:\n{instruction}"
    )

    async with ctx.typing():

        ai_response = await ask_ai(
            prompt,
            system_prompt
        )

    if ai_response.startswith("❌"):
        await ctx.send(ai_response)
        return

    # Remove Markdown fences if the model adds them.
    cleaned_code = re.sub(
        r"^```(?:\w+)?\s*|\s*```$",
        "",
        ai_response.strip()
    )

    if not cleaned_code:
        await ctx.send(
            "❌ مدل کد معتبری تولید نکرد."
        )
        return

    # Prevent accidental oversized output.
    if len(cleaned_code) > MAX_AI_OUTPUT:
        await ctx.send(
            "❌ خروجی AI بیش از حد مجاز است. "
            "فایل را به بخش‌های کوچک‌تر تقسیم کن."
        )
        return

    preview = cleaned_code[:1200]

    await ctx.send(
        "📝 **پیش‌نمایش تغییرات تولیدشده:**\n"
        f"```text\n{preview}\n```\n"
        "برای ثبت این تغییر، دستور زیر را ارسال کن:\n"
        "`!تأییدتغییر`"
    )

    # Save proposed change in memory for later confirmation.
    pending_edits[ctx.author.id] = {
        "filepath": filepath,
        "content": cleaned_code,
        "sha": sha,
        "instruction": instruction,
        "channel_id": ctx.channel.id,
    }


pending_edits = {}


@bot.command(name="تأییدتغییر")
async def confirm_edit(ctx):

    edit = pending_edits.get(
        ctx.author.id
    )

    if not edit:
        await ctx.send(
            "❌ هیچ تغییر در انتظاری برای تأیید وجود ندارد."
        )
        return

    if edit["channel_id"] != ctx.channel.id:
        await ctx.send(
            "❌ تأیید باید در همان کانالی انجام شود که تغییر در آن پیشنهاد شده."
        )
        return

    # Re-fetch the file to detect concurrent changes.
    latest_content, latest_sha = await get_github_file(
        edit["filepath"]
    )

    if latest_content is None or latest_sha != edit["sha"]:
        pending_edits.pop(ctx.author.id, None)

        await ctx.send(
            "⚠️ فایل در GitHub از زمان تولید پیشنهاد تغییر کرده است. "
            "لطفاً پیشنهاد جدیدی تولید کن."
        )
        return

    success = await update_github_file(
        edit["filepath"],
        edit["content"],
        edit["sha"],
        f"AI Update: {edit['instruction'][:50]}"
    )

    pending_edits.pop(
        ctx.author.id,
        None
    )

    if success:
        await ctx.send(
            "✅ تغییر با موفقیت در GitHub ثبت شد.\n"
            f"📄 فایل: `{edit['filepath']}`"
        )
    else:
        await ctx.send(
            "❌ ثبت تغییر در GitHub ناموفق بود."
        )


# ============================================================
# 13. STARTUP AND SHUTDOWN
# ============================================================

async def main():

    logger.info("Starting Wifream-AI...")

    try:
        async with bot:
            await bot.start(DISCORD_TOKEN)

    finally:
        await close_session()


if __name__ == "__main__":

    try:
        import asyncio

        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Wifream-AI stopped by user.")

    except Exception:
        logger.exception(
            "Fatal error while starting Wifream-AI"
        )
