import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpEventType } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { HealthService } from '../../core/services/health.service';
import { AuthService } from '../../core/services/auth.service';
import { BookService, progressPercent } from '../../core/services/book.service'; 

const ALLOWED_EXTENSIONS = ['pdf', 'epub', 'docx', 'txt'];
const MAX_SIZE_MB = 50;

/**
 * Upload page: file picker + target-language selection, styled after the
 * reference screenshot. Phase 3 wires the actual upload — client-side
 * validation mirrors the backend's rules (extension + size) so the user
 * gets instant feedback instead of waiting on a round trip for an
 * error the frontend could have caught itself.
 */
@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './upload.component.html',
})
export class UploadComponent implements OnInit {
  backendStatus: 'checking' | 'online' | 'offline' = 'checking';

  languages = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'hi', label: 'Hindi', flag: '🇮🇳' },
    { code: 'te', label: 'Telugu', flag: '🇮🇳' },
    { code: 'ta', label: 'Tamil', flag: '🇮🇳' },
  ];
  selectedLanguage = this.languages[0].code;

  selectedFile: File | null = null;
  validationError: string | null = null;
  uploadError: string | null = null;
  uploadProgress: number | null = null;
  uploadedTitle: string | null = null;
  isDragging = false;

  constructor(
    private healthService: HealthService,
    private auth: AuthService,
    private bookService: BookService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.healthService.check().subscribe({
      next: () => (this.backendStatus = 'online'),
      error: () => (this.backendStatus = 'offline'),
    });
  }

  selectLanguage(code: string): void {
    this.selectedLanguage = code;
  }

  onFileInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.handleFile(file);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(): void {
    this.isDragging = false;
  }

  private handleFile(file: File): void {
    this.validationError = null;
    this.uploadError = null;
    this.uploadedTitle = null;

    const extension = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      this.validationError = `Unsupported file type ".${extension}". Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
      this.selectedFile = null;
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      this.validationError = `File is too large. Max size is ${MAX_SIZE_MB}MB.`;
      this.selectedFile = null;
      return;
    }

    this.selectedFile = file;
  }

  submit(): void {
    if (!this.selectedFile) {
      return;
    }
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }

    this.uploadError = null;
    this.uploadProgress = 0;

    this.bookService.upload(this.selectedFile).subscribe({
      next: (event) => {
        const percent = progressPercent(event);
        if (percent !== null) {
          this.uploadProgress = percent;
        }
        if (event.type === HttpEventType.Response && event.body) {
          this.uploadedTitle = event.body.title;
          this.uploadProgress = null;
          this.selectedFile = null;
        }
      },
      error: (err) => {
        this.uploadProgress = null;
        this.uploadError = err?.error?.detail ?? 'Upload failed. Please try again.';
      },
    });
  }

  clearFile(): void {
    this.selectedFile = null;
    this.validationError = null;
  }
}