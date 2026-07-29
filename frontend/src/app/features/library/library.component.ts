import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Book, BookService } from '../../core/services/book.service';

interface BookCard {
  id: string;
  title: string;
  author: string;
  coverColor: string;
}

/**
 * Library grid, styled after the Kindle reference screenshot and backed by
 * the real GET /books endpoint so uploaded books appear immediately.
 */
@Component({
  selector: 'app-library',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './library.component.html',
})
export class LibraryComponent implements OnInit {
  filters = ['All Titles', 'Books', 'Audiobooks', 'Samples'];
  activeFilter = 'All Titles';

  books: BookCard[] = [];

  constructor(private bookService: BookService) {}

  ngOnInit(): void {
    this.bookService.list().subscribe({
      next: (response) => {
        this.books = response.items.map((book) => ({
          id: book.id,
          title: book.title || book.original_filename,
          author: book.author || 'Unknown author',
          coverColor: this.coverColorForStatus(book.status),
        }));
      },
      error: () => {
        this.books = [];
      },
    });
  }

  setFilter(filter: string): void {
    this.activeFilter = filter;
  }

  private coverColorForStatus(status: Book['status']): string {
    switch (status) {
      case 'parsed':
        return '#0f766e';
      case 'parsing':
        return '#92400e';
      case 'failed':
        return '#b91c1c';
      default:
        return '#1f2937';
    }
  }
}