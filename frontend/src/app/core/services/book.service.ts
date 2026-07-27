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
  status: string;
  created_at: string;
}

export interface BookListResponse {
  items: Book[];
  total: number;
}

/**
 * Handles book upload + retrieval. Upload uses HttpClient's low-level
 * `request()` with `reportProgress: true` so the upload page can show a
 * real progress bar instead of an indeterminate spinner.
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
}

/** Helper used by the upload component to turn HttpEvents into a % figure. */
export function progressPercent(event: HttpEvent<unknown>): number | null {
  if (event.type === HttpEventType.UploadProgress && event.total) {
    return Math.round((100 * event.loaded) / event.total);
  }
  return null;
}