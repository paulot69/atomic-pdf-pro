import subprocess
import asyncio
import sys
import logging
from typing import AsyncGenerator, List, Optional

logger = logging.getLogger(__name__)

class RunnerService:
    async def run_single(self,
                         filepath: str,
                         title: str,
                         author: str = "",
                         year: str = "",
                         index_content: str = "",
                         no_ai: bool = False,
                         translate_to: str = "") -> AsyncGenerator[str, None]:
        """
        Runs main.py for a single book.
        Yields output lines for WebSocket streaming.
        """

        # Construct the command
        cmd = [sys.executable, "main.py", filepath]

        if title:
            cmd.extend(["--titulo", title])
        if author:
            cmd.extend(["--autor", author])
        if year:
            cmd.extend(["--ano", str(year)])

        # Advanced Options
        if no_ai:
            cmd.extend(["--sin-ia"])

        if translate_to and translate_to.strip():
            cmd.extend(["--traducir-a", translate_to.strip()])

        yield f"🚀 Iniciando proceso para: {title}\n"
        yield f"📂 Archivo: {filepath}\n"
        yield f"⚙️  Opciones: IA={'OFF' if no_ai else 'ON'}, Traducción={translate_to or 'OFF'}\n"

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Stream stdout
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    yield f"{decoded}\n"

            # Stream stderr (usually errors or logs)
            stderr_out = await process.stderr.read()
            if stderr_out:
                yield f"⚠️ ERROR/LOG:\n{stderr_out.decode('utf-8', errors='replace')}\n"

            await process.wait()
            if process.returncode == 0:
                yield "✅ Proceso finalizado con éxito.\n"
            else:
                yield f"❌ El proceso falló con código {process.returncode}.\n"

        except Exception as e:
            yield f"❌ Error crítico ejecutando el script: {e}\n"

    async def run_batch(self, books: List[dict], no_ai: bool = False, translate_to: str = "") -> AsyncGenerator[str, None]:
        """
        Runs main.py for a list of books sequentially.
        """
        yield f"📚 Iniciando proceso BATCH para {len(books)} libros.\n"
        yield f"⚙️  Configuración Global: IA={'OFF' if no_ai else 'ON'}, Traducción={translate_to or 'OFF'}\n"

        for i, book in enumerate(books):
            yield f"\n[{i+1}/{len(books)}] Procesando: {book.get('title', 'Sin Título')}\n"
            yield "--------------------------------------------------\n"

            async for line in self.run_single(
                filepath=book.get('local_path', ''),
                title=book.get('title', ''),
                author=book.get('author', ''),
                year=book.get('year', ''),
                no_ai=no_ai,
                translate_to=translate_to
            ):
                yield line

            yield "--------------------------------------------------\n"

        yield "🏁 Proceso Batch finalizado.\n"
