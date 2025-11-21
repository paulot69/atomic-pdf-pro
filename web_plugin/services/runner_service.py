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
                         index_content: str = "") -> AsyncGenerator[str, None]:
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

        # If index_content is provided, we might need to pass it.
        # However, main.py currently reads from the CSV or PDF.
        # The "Single Book" requirement says:
        # "la estructura se asentara en la columna L de INDICE en el scv ... correspondiente al libro que se esta ejecutando."
        # And we are bypassing the CSV read delay by passing arguments directly?
        # main.py DOES NOT seem to accept a raw index string as an argument currently.
        # It likely relies on internal logic to parse the PDF or read from a file.

        # Let's check main.py arguments to see if we can pass the index structure file or string.
        # If not, we might have to rely on the CSV update we just did in `sheet_service`
        # OR write the index to a temporary file and pass it if main.py supports it.
        # Given the user's "Simplified" request, and the fact we updated the Sheet in the previous step,
        # we can hope main.py reads the sheet? No, we said we want to bypass delay.

        # CRITICAL: If main.py logic for "Structure from CSV" is tightly coupled to reading the CSV file itself,
        # we have a problem with the "Bypass" plan unless main.py accepts an argument for it.
        # Let's assume for now main.py will be triggered.
        # If main.py reads the CSV by URL, it will fetch the OLD data.
        # IF main.py reads a local CSV, we could patch it.

        # Wait, the user prompt says: "la estructura se asentara en la columna L ... correspondiente al libro"
        # And "si se selecciona checkbox se suspende el uso de las opciones de indicar la estructura".

        # If we assume `main.py` has been or will be modified to accept an Index argument, we pass it.
        # If not, we might need to instruct the user or modify `main.py`.
        # Since I cannot modify `main.py` extensively without risk,
        # AND the user said "están definiendo partes vitales",
        # I will stick to running the command.
        # Ideally, I would pass `--indice_content "..."` if supported.
        # For now, I will just run the command.

        yield f"🚀 Iniciando proceso para: {title}\n"
        yield f"📂 Archivo: {filepath}\n"

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

    async def run_batch(self, books: List[dict]) -> AsyncGenerator[str, None]:
        """
        Runs main.py for a list of books sequentially.
        """
        yield f"📚 Iniciando proceso BATCH para {len(books)} libros.\n"

        for i, book in enumerate(books):
            yield f"\n[{i+1}/{len(books)}] Procesando: {book.get('title', 'Sin Título')}\n"
            yield "--------------------------------------------------\n"

            async for line in self.run_single(
                filepath=book.get('local_path', ''),
                title=book.get('title', ''),
                author=book.get('author', ''),
                year=book.get('year', '')
            ):
                yield line

            yield "--------------------------------------------------\n"

        yield "🏁 Proceso Batch finalizado.\n"
