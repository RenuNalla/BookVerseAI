import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  loading = false;
  errorMessage: string | null = null;

  get form(): FormGroup {
    return this.fb.group({
      full_name: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
    });
  }

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router
  ) {}

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading = true;
    this.errorMessage = null;

    const raw = this.form.getRawValue() as {
      full_name: string;
      email: string;
      password: string;
    };

    this.auth.register(raw).subscribe({
      next: () => {
        // Explicit login step after registration keeps the two flows
        // independently testable and mirrors what the backend expects.
        this.auth.login({ email: raw.email, password: raw.password }).subscribe({
          next: () => this.router.navigate(['/library']),
          error: () => this.router.navigate(['/login']),
        });
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail ?? 'Registration failed. Please try again.';
      },
    });
  }
}
