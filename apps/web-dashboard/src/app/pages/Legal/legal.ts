import { Component, HostListener } from '@angular/core';

@Component({
  selector: 'app-legal',
  templateUrl: './legal.html',
  styleUrl: './legal.css',
})
export class Legal {
  activeSection = 'overview';

  @HostListener('window:scroll')
  onScroll(): void {
    const sections = [
      'overview',
      'data-collected',
      'data-use',
      'sharing',
      'retention',
      'user-rights',
      'self-hosting',
      'contact',
    ];

    const current = sections
      .map((id) => ({ id, top: document.getElementById(id)?.getBoundingClientRect().top ?? Number.MAX_VALUE }))
      .filter((section) => section.top <= 120)
      .pop();

    if (current) {
      this.activeSection = current.id;
    }
  }

  scrollTo(sectionId: string, event: Event): void {
    event.preventDefault();
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}
