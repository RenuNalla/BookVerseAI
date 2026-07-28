import { HttpClient, HttpEvent, HttpEventType, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';


export interface Book {
  id: string;
  title: string;
  author: string | null;
  original_filename: string;
  file_extension: string;
  file_size_bytes: number;
  page_count: number | null;
  source_language: string;
  status: 'uploaded' | 'parsing' | 'parsed' | 'translating' | 'ready' | 'failed';
  error_message: string | null;
  created_at: string;}

export interface BookListResponse {
  items: Book[];
  total: number;
}

export interface Chapter {
  id: string;
  chapter_index: number;
  title: string;
  word_count: number;
}

export interface ChapterDetail extends Chapter {
  content: string;
}

export interface ChapterListResponse {
  items: Chapter[];
  total: number;
}

/**
 * Handles book upload + retrieval, plus the chapters produced by Phase 4
 * parsing. Upload uses HttpClient's low-level `request()` with
 * `reportProgress: true` so the upload page can show a real progress bar.
 */
@Injectable({ providedIn: 'root' })
export class BookService {
  constructor(private http: HttpClient) {}

  upload(file: File): Observable<HttpEvent<Book>> {
    const formData = new FormData();
    formData.append('file', file);

    const req = new HttpRequest('POST', `${environment.apiBaseUrl}/books/upload`, formData, {
      reportProgress: true,
    });
    return this.http.request<Book>(req);
  }

  list(): Observable<BookListResponse> {
    return this.http.get<BookListResponse>(`${environment.apiBaseUrl}/books`);
  }

  get(id: string): Observable<Book> {
    return this.http.get<Book>(`${environment.apiBaseUrl}/books/${id}`);
  }

  reparse(id: string): Observable<Book> {
    return this.http.post<Book>(`${environment.apiBaseUrl}/books/${id}/reparse`, {});
  }

  getChapters(bookId: string): Observable<ChapterListResponse> {
    return this.http.get<ChapterListResponse>(`${environment.apiBaseUrl}/books/${bookId}/chapters`);
  }

  getChapterDetail(bookId: string, chapterId: string): Observable<ChapterDetail> {
    return this.http.get<ChapterDetail>(
      `${environment.apiBaseUrl}/books/${bookId}/chapters/${chapterId}`
    );
  }
}

/** Helper used by the upload component to turn HttpEvents into a % figure. */
export function progressPercent(event: HttpEvent<unknown>): number | null {
  if (event.type === HttpEventType.UploadProgress && event.total) {
    return Math.round((100 * event.loaded) / event.total);
  }
  return null;
}