import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Book, BookService, Chapter } from '../../core/services/book.service';

/**
 * Shows a book's metadata + the chapters produced by Phase 4 parsing.
 * Intentionally minimal — this becomes the actual reading interface in
 * Phase 7, so it's not worth over-building the UI here.
 */
@Component({
  selector: 'app-book-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './book-detail.component.html',
})
export class BookDetailComponent implements OnInit {
  book: Book | null = null;
  chapters: Chapter[] = [];
  loading = true;
  errorMessage: string | null = null;

  constructor(private route: ActivatedRoute, private bookService: BookService) {}

  ngOnInit(): void {
    const bookId = this.route.snapshot.paramMap.get('id');
    if (!bookId) {
      this.errorMessage = 'No book id in the URL.';
      this.loading = false;
      return;
    }

    this.bookService.get(bookId).subscribe({
      next: (book) => {
        this.book = book;
        this.bookService.getChapters(bookId).subscribe({
          next: (res) => {
            this.chapters = res.items;
            this.loading = false;
          },
          error: () => {
            this.loading = false;
          },
        });
      },
      error: () => {
        this.errorMessage = 'Could not load this book.';
        this.loading = false;
      },
    });
  }
}