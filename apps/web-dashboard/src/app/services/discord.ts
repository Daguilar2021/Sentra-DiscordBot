import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DiscordService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:5121/api/invite';

  getInviteUrl(): Observable<string> {
    return this.http.get<{ url: string }>(this.apiUrl).pipe(
      map(response => response.url)
    );
  }
}
