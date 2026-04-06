"""
EML Attachment Extractor
Parses .eml files, extracts all attachments (Word, Excel, PDF, PPT, images, etc.)
and prints the email body text.

Usage:
    python eml_attachment_extractor.py <eml_file_or_folder> [--output <output_dir>]

    If a folder is given, all .eml files in the folder are processed.
    Attachments are saved to <output_dir>/<email_subject_sanitized>/
"""

import email
import email.policy
import os
import sys
import re
import argparse
import quopri
from pathlib import Path
from email import message_from_file
from email.header import decode_header


def sanitize_filename(name: str) -> str:
    """Remove characters that aren't safe for filenames."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.strip('. ')
    return name[:100] if name else 'unnamed'


def decode_header_value(value: str) -> str:
    """Decode RFC 2047 encoded header values."""
    if not value:
        return ''
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(part)
    return ' '.join(result)


def get_body_text(msg) -> str:
    """Extract plain text body from email message."""
    texts = []
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get('Content-Disposition', ''))
            if content_type == 'text/plain' and 'attachment' not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    texts.append(payload.decode(charset, errors='replace'))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            texts.append(payload.decode(charset, errors='replace'))
    return '\n'.join(texts)


def extract_attachments(eml_path: str, output_dir: str) -> dict:
    """
    Parse an .eml file and extract:
    - Email metadata (from, to, cc, subject, date)
    - Body text
    - All attachments saved to output_dir

    Returns dict with metadata, body, and list of extracted files.
    """
    eml_path = Path(eml_path)

    with open(eml_path, 'r', encoding='utf-8', errors='replace') as f:
        msg = message_from_file(f)

    # Extract metadata
    subject = decode_header_value(msg.get('Subject', ''))
    from_addr = decode_header_value(msg.get('From', ''))
    to_addr = decode_header_value(msg.get('To', ''))
    cc_addr = decode_header_value(msg.get('CC', ''))
    date = msg.get('Date', '')

    # Create output folder per email
    folder_name = sanitize_filename(subject) if subject else eml_path.stem
    email_output_dir = Path(output_dir) / folder_name
    email_output_dir.mkdir(parents=True, exist_ok=True)

    # Extract body
    body = get_body_text(msg)

    # Save body as text file
    body_file = email_output_dir / '_email_body.txt'
    with open(body_file, 'w', encoding='utf-8') as f:
        f.write(f"From: {from_addr}\n")
        f.write(f"To: {to_addr}\n")
        f.write(f"CC: {cc_addr}\n")
        f.write(f"Date: {date}\n")
        f.write(f"Subject: {subject}\n")
        f.write(f"\n{'='*80}\n\n")
        f.write(body)

    # Extract attachments
    extracted_files = []
    attachment_counter = 0

    for part in msg.walk():
        content_type = part.get_content_type()
        disposition = str(part.get('Content-Disposition', ''))
        filename = part.get_filename()

        # Skip text parts that aren't attachments
        if content_type in ('text/plain', 'text/html') and 'attachment' not in disposition:
            continue

        # Skip multipart containers
        if part.get_content_maintype() == 'multipart':
            continue

        # Get payload
        payload = part.get_payload(decode=True)
        if not payload:
            continue

        # Determine filename
        if filename:
            filename = decode_header_value(filename)
        else:
            # Skip inline images without meaningful content
            if content_type.startswith('image/') and 'attachment' not in disposition:
                continue
            # Generate filename from content type
            ext_map = {
                'application/pdf': '.pdf',
                'application/msword': '.doc',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'application/vnd.ms-excel': '.xls',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                'application/vnd.ms-powerpoint': '.ppt',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/gif': '.gif',
            }
            ext = ext_map.get(content_type, '.bin')
            attachment_counter += 1
            filename = f'attachment_{attachment_counter}{ext}'

        filename = sanitize_filename(filename)
        filepath = email_output_dir / filename

        # Handle duplicate filenames
        if filepath.exists():
            stem = filepath.stem
            suffix = filepath.suffix
            counter = 1
            while filepath.exists():
                filepath = email_output_dir / f"{stem}_{counter}{suffix}"
                counter += 1

        with open(filepath, 'wb') as f:
            f.write(payload)

        extracted_files.append({
            'filename': filename,
            'content_type': content_type,
            'size': len(payload),
            'path': str(filepath),
        })

    return {
        'eml_file': str(eml_path),
        'subject': subject,
        'from': from_addr,
        'to': to_addr,
        'cc': cc_addr,
        'date': date,
        'body_preview': body[:500] if body else '',
        'body_file': str(body_file),
        'attachments': extracted_files,
    }


def process_folder(folder_path: str, output_dir: str) -> list:
    """Process all .eml files in a folder."""
    folder = Path(folder_path)
    results = []

    eml_files = list(folder.glob('*.eml'))
    if not eml_files:
        print(f"No .eml files found in {folder}")
        return results

    print(f"Found {len(eml_files)} .eml file(s) in {folder}\n")

    for eml_file in sorted(eml_files):
        print(f"{'='*80}")
        print(f"Processing: {eml_file.name}")
        print(f"{'='*80}")

        try:
            result = extract_attachments(str(eml_file), output_dir)
            results.append(result)

            print(f"  Subject: {result['subject']}")
            print(f"  From:    {result['from']}")
            print(f"  Date:    {result['date']}")
            print(f"  Body:    {result['body_file']}")

            if result['attachments']:
                print(f"  Attachments ({len(result['attachments'])}):")
                for att in result['attachments']:
                    size_kb = att['size'] / 1024
                    print(f"    - {att['filename']} ({att['content_type']}, {size_kb:.1f} KB)")
                    print(f"      Saved: {att['path']}")
            else:
                print("  No attachments found.")

            print()

        except Exception as e:
            print(f"  ERROR: {e}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description='Extract attachments from .eml files')
    parser.add_argument('path', help='Path to .eml file or folder containing .eml files')
    parser.add_argument('--output', '-o', default=None, help='Output directory (default: same as input)')
    args = parser.parse_args()

    input_path = Path(args.path)

    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        sys.exit(1)

    if args.output:
        output_dir = args.output
    elif input_path.is_dir():
        output_dir = str(input_path / '_extracted')
    else:
        output_dir = str(input_path.parent / '_extracted')

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        results = process_folder(str(input_path), output_dir)
    else:
        result = extract_attachments(str(input_path), output_dir)
        results = [result]

        print(f"Subject: {result['subject']}")
        print(f"From:    {result['from']}")
        print(f"Date:    {result['date']}")
        print(f"Body:    {result['body_file']}")

        if result['attachments']:
            print(f"\nAttachments ({len(result['attachments'])}):")
            for att in result['attachments']:
                size_kb = att['size'] / 1024
                print(f"  - {att['filename']} ({att['content_type']}, {size_kb:.1f} KB)")
                print(f"    Saved: {att['path']}")
        else:
            print("\nNo attachments found.")

    total_attachments = sum(len(r['attachments']) for r in results)
    print(f"\n{'='*80}")
    print(f"SUMMARY: {len(results)} email(s) processed, {total_attachments} attachment(s) extracted")
    print(f"Output: {output_dir}")


if __name__ == '__main__':
    main()
