from pathlib import Path

import whisper
from whisper import transcribe

from DataProcessing import AUDIO_EXTENSIONS
from Utility.Logger import Logger


def TranscribeAudioFolder(
    input_dir: Path,
    out_dir: Path,
    model_size: str = "small",
    overwrite: bool = False,
):
    """
    Transcribes all audio projects in a folder structure using OpenAI Whisper.

    Args:
        input_dir (Path): Directory containing project subfolders with audio chunks.
        out_dir (Path): Output directory where transcriptions will be saved.
        model_size (str): Whisper model size (e.g., 'tiny', 'base', 'small', 'medium', 'large').
        overwrite (bool): Whether to overwrite existing transcriptions.
    """
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    Logger.info(f"Loading Whisper model: {model_size}")
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        Logger.error(f"Failed to load Whisper model '{model_size}': {e}")
        return

    projects = [p for p in input_dir.iterdir() if p.is_dir()]
    if not projects:
        Logger.warning(f"No projects found in {input_dir}")
        return

    Logger.info(f"Found {len(projects)} projects to process in '{input_dir}'")

    failed_projects = []

    for project in projects:
        project_name = project.name
        Logger.info(f"Processing project: {project_name}")

        project_out_dir = out_dir / project_name
        transcripts_dir = project_out_dir / "transcripts"
        transcripts_dir.mkdir(parents=True, exist_ok=True)

        chunks = sorted(
            [f for f in project.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
        )
        if not chunks:
            Logger.warning(f"No audio chunks found in '{project_name}'. Skipping.")
            failed_projects.append(project_name)
            continue

        combined_transcription = []

        for idx, chunk_file in enumerate(chunks, start=1):
            txt_file = transcripts_dir / f"{chunk_file.stem}.txt"

            if txt_file.exists() and not overwrite:
                Logger.info(f"Transcript for '{chunk_file.name}' already exists. Skipping.")
                continue

            try:
                Logger.info(f"Transcribing chunk {idx}/{len(chunks)}: {chunk_file.name}")
                result = transcribe(str(chunk_file))
                transcription = result.get("text", "").strip()

                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(transcription)

                combined_transcription.append(transcription)

            except Exception as e:
                Logger.error(f"Error transcribing '{chunk_file.name}': {e}")
                failed_projects.append(project_name)
                break

        # Save combined transcription for project
        if combined_transcription:
            project_txt = project_out_dir / f"{project_name}.txt"
            if project_txt.exists() and not overwrite:
                Logger.info(f"Combined transcription already exists for '{project_name}'. Skipping.")
            else:
                with open(project_txt, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(combined_transcription))
                Logger.info(f"Combined transcription saved to: {project_txt}")

    Logger.info("Transcription complete.")
    if failed_projects:
        Logger.warning(f"{len(failed_projects)} projects failed:")
        for p in failed_projects:
            Logger.warning(f"  - {p}")
    else:
        Logger.info("All projects processed successfully.")
