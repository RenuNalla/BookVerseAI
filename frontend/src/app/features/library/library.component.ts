import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

interface BookCard {
  title: string;
  author: string;
  coverColor: string; // placeholder swatch until real cover images exist
}

/**
 * Library grid, styled after the Kindle reference screenshot (sidebar
 * filters + card grid). Uses static placeholder data for now — replaced
 * with a real BookService call to GET /books in Phase 7.
 */
@Component({
  selector: 'app-library',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './library.component.html',
})
export class LibraryComponent {
  filters = ['All Titles', 'Books', 'Audiobooks', 'Samples'];
  activeFilter = 'All Titles';

  books: BookCard[] = [
    { title: 'Atomic Habits (Telugu)', author: 'James Clear', coverColor: '#1f2937' },
    { title: 'Deep Work (Hindi)', author: 'Cal Newport', coverColor: '#fef3c7' },
    { title: 'Operations Research', author: 'R. Panneerselvam', coverColor: '#78350f' },
    { title: 'Ponniyin Selvan Retold', author: 'Kalki', coverColor: '#7c2d12' },
  ];

  setFilter(filter: string): void {
    this.activeFilter = filter;
  }
}