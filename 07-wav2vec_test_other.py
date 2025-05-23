# -*- coding: utf-8 -*-
"""Wav2vec-test other

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1vpkH6AtDae2DP6BsMJA81D6JGq6ezSTo
"""

import torch
import torchaudio
from torchaudio.datasets import LIBRISPEECH
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Try to import jiwer (for accurate WER), otherwise use custom WER
try:
    from jiwer import wer
    print("✅ Using 'jiwer' for accurate WER calculation.")
    compute_wer = wer  # Use jiwer's WER if available
except ImportError:
    print("⚠️ 'jiwer' not installed. Using simplified WER calculation.")
    def compute_wer(reference, hypothesis):
        """Fallback WER calculation if jiwer is missing."""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()

        # Total words in reference (denominator)
        total_ref_words = len(ref_words)
        if total_ref_words == 0:
            return 0.0

        # Count matching words (simplified approach)
        correct = sum(1 for r, h in zip(ref_words, hyp_words) if r == h)
        errors = max(len(ref_words), len(hyp_words)) - correct
        return errors / total_ref_words

# Load LibriSpeech test-other dataset
dataset = LIBRISPEECH("./", url="test-other", download=True)
print(f"Total samples in LibriSpeech 'test-other': {len(dataset)}")

# Load Wav2Vec 2.0 model and processor
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

def transcribe_audio(waveform, sample_rate):
    """Transcribes audio using Wav2Vec 2.0."""
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)

    input_values = processor(waveform.squeeze().numpy(), return_tensors="pt", sampling_rate=16000).input_values

    with torch.no_grad():
        logits = model(input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    return transcription.strip()

# Limit samples for testing (optional)
num_samples = len(dataset)  # Full dataset (2,939 samples)
# num_samples = 10  # Test on a smaller subset (recommended for quick checks)

results = []

for i in range(num_samples):
    waveform, sample_rate, transcript, _, _, _ = dataset[i]

    try:
        wav2vec_text = transcribe_audio(waveform, sample_rate)

        # Compute WER (using jiwer if available, otherwise custom)
        error_rate = compute_wer(transcript.lower(), wav2vec_text.lower())

        results.append({
            "index": i,
            "WER": error_rate,
            "Reference": transcript,
            "Wav2Vec Output": wav2vec_text
        })

        # Print detailed transcription comparison
        print(f"\n--- Sample {i + 1}/{num_samples} ---")
        print(f"▶ Ground Truth: {transcript}")
        print(f"▶ Wav2Vec Output: {wav2vec_text}")
        print(f"▶ WER: {error_rate:.3f}")

    except Exception as e:
        print(f"❌ Error processing sample {i}: {str(e)}")
        continue

# Display results in a DataFrame
import pandas as pd
results_df = pd.DataFrame(results)
display(results_df)

# Calculate and print average WER
if results:
    avg_wer = results_df["WER"].mean()
    print(f"\n📊 Average Word Error Rate (WER): {avg_wer:.3f}")

'''valuation Result (Wav2Vec on LibriSpeech "test-other")

This script was used to evaluate the performance of the Wav2Vec model on the "test-other" subset of the LibriSpeech dataset, comprising 2939 audio samples. The model generated transcriptions for each sample, and the Word Error Rate (WER) was calculated individually for each one.

After aggregating the results, the average WER was approximately 0.101 (i.e., 10.1%).  this WER metric is not ideal.'''
